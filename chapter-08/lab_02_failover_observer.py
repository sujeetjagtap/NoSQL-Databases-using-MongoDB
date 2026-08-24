"""Lab 8.2 - Observe Failover and Election
PyMongo failover observer script.
Requires a running replica set (use Lab 8.1 docker-compose).
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient, ReadPreference
from config.connection import banner

RS_URI = os.getenv(
    "REPLICA_SET_URI",
    "mongodb://host.docker.internal:27017,host.docker.internal:27018,host.docker.internal:27019/?replicaSet=rs0"
)


def get_rs_status(client):
    """Get replica set member statuses."""
    status = client.admin.command("replSetGetStatus")
    members = []
    for m in status["members"]:
        members.append({
            "name": m["name"],
            "state_str": m["stateStr"],
            "health": m["health"],
        })
    return members


def observe_failover(interval=2, duration=60):
    """Monitor replica set state and detect primary changes."""
    print(f"Connecting to: {RS_URI}")
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=5000,
                         socketTimeoutMS=3000, connectTimeoutMS=5000)
    client.admin.command("ping")
    print("[OK] Connected to replica set.")
    print(f"Monitoring every {interval}s for {duration}s...")
    print("[TIP] In another terminal, run:")
    print('  mongosh --host localhost --port 27017 --eval \'rs.stepDown()\'')
    print()

    last_primary = None
    start = time.time()
    try:
        while time.time() - start < duration:
            try:
                members = get_rs_status(client)
                primary = None
                for m in members:
                    if m["state_str"] == "PRIMARY":
                        primary = m["name"]
                if primary and primary != last_primary:
                    ts = time.strftime("%H:%M:%S")
                    if last_primary is None:
                        print(f"  [{ts}] PRIMARY detected: {primary}")
                    else:
                        print(f"  [{ts}] *** FAILOVER: {last_primary} -> {primary} ***")
                    last_primary = primary
                time.sleep(interval)
            except Exception as e:
                print(f"  [WARN] Connection issue: {e}")
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    print(f"\nMonitoring stopped. Final primary: {last_primary}")
    client.close()


def demo_write_read_concerns():
    """Demonstrate write concern and read concern settings."""
    print("\n=== Write/Read Concern Demo ===")
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=5000)
    db = client["failover_test"]
    db.drop_collection("test_data")
    col = db["test_data"]

    # w:1 (default)
    start = time.perf_counter()
    col.insert_one({"value": 1}, write_concern={"w": 1})
    t_w1 = time.perf_counter() - start
    print(f"  w:1 write: {t_w1*1000:.2f} ms")

    # w:majority
    start = time.perf_counter()
    col.insert_one({"value": 2}, write_concern={"w": "majority"})
    t_wm = time.perf_counter() - start
    print(f"  w:majority write: {t_wm*1000:.2f} ms")

    # Read from secondary
    col.insert_one({"concern": "read_test"})
    sec_client = MongoClient(RS_URI, serverSelectionTimeoutMS=5000,
                             read_preference=ReadPreference.SECONDARY_PREFERRED)
    sec_col = sec_client["failover_test"]["test_data"]
    time.sleep(1)
    result = sec_col.find_one({"concern": "read_test"})
    print(f"  Read from secondary: {result}")
    sec_client.close()
    client.close()


def main():
    banner("Lab 8.2: Observe Failover and Election")
    observe_failover(interval=2, duration=60)
    demo_write_read_concerns()
    banner("Lab 8.2 Complete")


if __name__ == "__main__":
    main()