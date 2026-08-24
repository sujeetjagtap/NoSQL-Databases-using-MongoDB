"""Lab 7.2 - Working Set Analysis
Insert 100K docs, check WiredTiger cache metrics via serverStatus."""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console

console = Console()


def main():
    banner("Lab 7.2: Working Set Analysis")
    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "working_set_docs")

    # Insert 100K x ~2KB documents
    count = 100000
    print(f"Inserting {count:,} documents (~2KB each)...")
    docs = [{"sensor": f"S-{i:06d}", "reading": i * 0.01, "metadata": "x" * 1800} for i in range(count)]
    start = time.perf_counter()
    col.insert_many(docs)
    elapsed = time.perf_counter() - start
    print(f"[OK] Inserted {count:,} docs in {elapsed:.1f}s ({count/elapsed:,.0f} docs/sec)")

    # WiredTiger cache stats
    status = db.command("serverStatus")
    wt = status.get("wiredTiger", {})
    cache = wt.get("cache", {})

    print("\n=== WiredTiger Cache Metrics ===")
    print(f"  Cache max:          {cache.get('maximum bytes configured', 'N/A'):>15,} bytes")
    print(f"  Cache in use:       {cache.get('bytes currently in the cache', 'N/A'):>15,} bytes")
    print(f"  Dirty bytes:        {cache.get('tracked dirty bytes in the cache', 'N/A'):>15,} bytes")
    print(f"  Pages evicted:      {cache.get('eviction pages evicted by application threads', 0):>15,}")
    print(f"  Pages read:         {cache.get('pages read into cache', 0):>15,}")

    # Simulate queries hitting different parts of working set
    print("\n=== Simulating Working Set Queries ===")
    for query_range in [(0, 1000), (49000, 50000), (99000, 100000)]:
        start = time.perf_counter()
        list(col.find({"sensor": {"$gte": f"S-{query_range[0]:06d}", "$lte": f"S-{query_range[1]:06d}"}}))
        elapsed = time.perf_counter() - start
        print(f"  Range {query_range[0]:>6}-{query_range[1]:<6}: {elapsed*1000:.1f} ms")

    # Cache hit ratio
    cache_after = db.command("serverStatus")["wiredTiger"]["cache"]
    pages_read = cache_after.get('pages read into cache', 0)
    pages_evict = cache_after.get('eviction pages evicted by application threads', 0)
    print(f"\n  Pages read into cache: {pages_read:,}")
    print(f"  Pages evicted:         {pages_evict:,}")
    if pages_read > 0:
        hit_ratio = max(0, 1 - (pages_evict / pages_read))
        print(f"  Approx cache hit ratio: {hit_ratio:.1%}")
    print(f"  [TIP] If working set > cache, hit ratio drops and evictions increase.")

    banner("Lab 7.2 Complete")


if __name__ == "__main__":
    main()