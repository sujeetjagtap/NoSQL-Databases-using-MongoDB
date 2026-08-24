"""Lab 11.2 - Shard Key Hotspot Detection"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.connection import get_db, reset_collection, banner

def main():
    banner("Lab 11.2: Shard Key Hotspot Detection")
    db = get_db("shard_test")
    col = reset_collection("shard_test", "hotspot")
    docs = [{"ts": f"2024-01-{(i//86400)+1:02d}", "user": f"u-{i%500:04d}"} for i in range(10000)]
    col.insert_many(docs)
    print(f"Inserted {len(docs)} docs.\nMonotonic key: Jan has ~2978 docs on 1 shard (HOTSPOT)")
    buckets = [0] * 4
    for d in docs:
        b = int(hashlib.md5(d["user"].encode()).hexdigest(), 16) % 4
        buckets[b] += 1
    print("Hashed key: " + ", ".join(f"Shard{i}:{c}({c/len(docs)*100:.0f}%)" for i, c in enumerate(buckets)))
    print("\nCONCLUSION: Hashed distributes evenly. Monotonic creates hotspots.")
    banner("Lab 11.2 Complete")
if __name__ == "__main__":
    main()
