"""Lab 10.2 - Inventory Reservation with Transactions"""
import sys, os, time, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pymongo import MongoClient, WriteConcern
from config.connection import banner
URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

def reserve(client, sku, qty, tid):
    session = client.start_session()
    db = client["inv_db"]
    try:
        with session.start_transaction(write_concern=WriteConcern(w="majority")):
            item = db.products.find_one({"sku": sku}, session=session)
            if item["stock"] < qty:
                return f"Thread-{tid}: INSUFFICIENT"
            db.products.update_one({"sku": sku}, {"$inc": {"stock": -qty}}, session=session)
            db.orders.insert_one({"sku": sku, "qty": qty, "tid": tid}, session=session)
            return f"Thread-{tid}: RESERVED"
    except Exception as e:
        return f"Thread-{tid}: CONFLICT"
    finally:
        session.end_session()

def main():
    banner("Lab 10.2: Inventory Reservation")
    client = MongoClient(URI, serverSelectionTimeoutMS=5000)
    db = client["inv_db"]
    db.products.drop()
    db.orders.drop()
    db.products.insert_many([{"sku": "LAPTOP", "stock": 5, "price": 999}])
    print("[OK] Seeded 1 product with 5 units.")
    print("\n=== 10 threads, each reserving 1 unit ===")
    results = []
    threads = []
    def run(tid):
        results.append(reserve(client, "LAPTOP", 1, tid))
    for i in range(10):
        t = threading.Thread(target=run, args=(i,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for r in results:
        print(f"  {r}")
    left = db.products.find_one({"sku": "LAPTOP"})["stock"]
    print(f"  Remaining: {left} | Orders: {db.orders.count_documents({})}")
    client.close()
    banner("Lab 10.2 Complete")
if __name__ == "__main__":
    main()
