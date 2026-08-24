"""Lab 9.1 - Measure Write Concern Latency
Insert 1,000 docs with w:1, w:majority, w:all. Compare latency.
Requires a running replica set (use Ch 8 docker-compose).
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient, WriteConcern
from config.connection import banner

RS_URI = os.getenv(
    "REPLICA_SET_URI",
    "mongodb://host.docker.internal:27017,host.docker.internal:27018,host.docker.internal:27019/?replicaSet=rs0"
)
DOC_COUNT = 1000


def benchmark_write_concern(client, wc_setting, journal, label):
    """Insert DOC_COUNT docs with given write concern and return avg latency."""
    db = client["cap_latency_test"]
    db.drop_collection(f"data_{label}")
    col = db[f"data_{label}"]
    wc = WriteConcern(w=wc_setting, j=journal)

    latencies = []
    for _ in range(DOC_COUNT):
        doc = {"value": time.time_ns(), "label": label}
        start = time.perf_counter()
        col.insert_one(doc, write_concern=wc)
        latencies.append(time.perf_counter() - start)

    avg_ms = (sum(latencies) / len(latencies)) * 1000
    p50_ms = sorted(latencies)[len(latencies) // 2] * 1000
    p99_ms = sorted(latencies)[int(len(latencies) * 0.99)] * 1000
    return avg_ms, p50_ms, p99_ms


def main():
    banner("Lab 9.1: Write Concern Latency Benchmark")
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print(f"[OK] Connected to replica set.")
    print(f"Inserting {DOC_COUNT:,} documents per configuration...")
    print()

    results = []

    # w:1, j:false
    avg, p50, p99 = benchmark_write_concern(client, 1, False, "w1_j0")
    results.append(("w:1, j:false", avg, p50, p99))
    print(f"  w:1, j:false done.")

    # w:1, j:true
    avg, p50, p99 = benchmark_write_concern(client, 1, True, "w1_j1")
    results.append(("w:1, j:true", avg, p50, p99))
    print(f"  w:1, j:true  done.")

    # w:majority, j:false
    avg, p50, p99 = benchmark_write_concern(client, "majority", False, "wmaj_j0")
    results.append(("w:majority, j:false", avg, p50, p99))
    print(f"  w:majority, j:false done.")

    # w:majority, j:true
    avg, p50, p99 = benchmark_write_concern(client, "majority", True, "wmaj_j1")
    results.append(("w:majority, j:true", avg, p50, p99))
    print(f"  w:majority, j:true  done.")

    # Print comparison table
    print(f"\n{'='*70}")
    print(f"  {'Configuration':<25} {'Avg (ms)':>10} {'P50 (ms)':>10} {'P99 (ms)':>10}")
    print(f"{'='*70}")
    for label, avg, p50, p99 in results:
        print(f"  {label:<25} {avg:>10.2f} {p50:>10.2f} {p99:>10.2f}")
    print(f"{'='*70}")

    print(f"\n  Key Takeaways:")
    print(f"  - w:1 is fastest (primary ack only)")
    print(f"  - w:majority adds ~2-5x latency (waits for secondary)")
    print(f"  - j:true adds minor overhead (disk flush)")
    print(f"  - Trade-off: consistency vs latency")

    client.close()
    banner("Lab 9.1 Complete")


if __name__ == "__main__":
    main()
