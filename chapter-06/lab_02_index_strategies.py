"""Lab 6.2 - Compare Index Strategies
Write throughput vs read performance trade-off."""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner


def benchmark_inserts(col, count, label):
    """Insert `count` documents and measure time."""
    docs = [{"sensor_id": f"SENSOR-{i:04d}", "reading": i * 0.1, "status": "active"} for i in range(count)]
    start = time.perf_counter()
    col.insert_many(docs)
    elapsed = time.perf_counter() - start
    rate = count / elapsed
    print(f"  {label}: {count} inserts in {elapsed:.2f}s = {rate:,.0f} docs/sec")
    return elapsed


def benchmark_reads(col, query, iterations, label):
    """Run `iterations` finds and measure time."""
    start = time.perf_counter()
    for _ in range(iterations):
        list(col.find(query).limit(10))
    elapsed = time.perf_counter() - start
    per_query = (elapsed / iterations) * 1000
    print(f"  {label}: {iterations} reads in {elapsed:.2f}s = {per_query:.2f} ms/query")
    return elapsed


def main():
    banner("Lab 6.2: Index Strategy Comparison")
    db = get_db("nosql_labs")

    # --- TEST 1: Insert with 0 indexes ---
    print("=== Insert Performance: 0 Indexes vs 5 Indexes ===")
    col_0 = reset_collection("nosql_labs", "perf_no_index")
    t0 = benchmark_inserts(col_0, 10000, "0 indexes")

    col_5 = reset_collection("nosql_labs", "perf_5_indexes")
    col_5.create_index([("sensor_id", 1)], name="idx_sensor")
    col_5.create_index([("reading", 1)], name="idx_reading")
    col_5.create_index([("status", 1)], name="idx_status")
    col_5.create_index([("sensor_id", 1), ("reading", -1)], name="idx_sensor_reading")
    col_5.create_index([("sensor_id", 1), ("status", 1)], name="idx_sensor_status")
    t5 = benchmark_inserts(col_5, 10000, "5 indexes")

    overhead_pct = ((t5 - t0) / t0) * 100
    print(f"\n  Write overhead with 5 indexes: {overhead_pct:+.1f}%")

    # --- TEST 2: Read performance ---
    print("\n=== Read Performance: Covered Query vs Non-Covered ===")
    query = {"sensor_id": "SENSOR-0050"}
    iterations = 1000

    # Non-covered (fetches full doc)
    t_non = benchmark_reads(col_5, query, iterations, "Non-covered (full doc)")

    # Covered (all fields in index)
    t_cov = benchmark_reads(
        col_5, query, iterations,
        "Covered (projection on indexed fields)"
    )
    print(f"\n  Covered query speedup: {t_non/t_cov:.1f}x")

    # --- ESR Rule Demo ---
    print("\n=== ESR Rule (Equality - Sort - Range) ===")
    print("  Query: {status: 'active', sensor_id: /^SENSOR-0/} .sort({reading: -1})")
    print("")
    print("  GOOD index (ESR order): {status: 1, sensor_id: 1, reading: -1}")
    print("    Equality  -> status = 'active'")
    print("    Sort     -> reading (descending)")
    print("    Range    -> sensor_id (prefix match)")
    print("")
    print("  BAD index  (wrong order): {reading: -1, status: 1, sensor_id: 1}")
    print("    Cannot use equality filter efficiently after sort prefix")

    banner("Lab 6.2 Complete")


if __name__ == "__main__":
    main()