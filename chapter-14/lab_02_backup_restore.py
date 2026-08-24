"""Lab 14.2 - Automated Backup and Restore Verification

A backup you have never restored is not a backup, it's a hope. This lab:
  1. Seeds a collection with known data and records a checksum.
  2. Takes a `mongodump` backup to a timestamped directory.
  3. Deliberately destroys the collection (simulating data loss).
  4. Restores from the backup with `mongorestore`.
  5. Verifies the restored data matches the original: same document
     count AND same content checksum (a restore that "succeeds" but
     silently drops or corrupts documents is worse than an obvious
     failure, so we don't just check the count).

Requires the MongoDB Database Tools (`mongodump` / `mongorestore`) to be
installed and on PATH in addition to a running `mongod`.
"""

import sys, os, subprocess, shutil, hashlib, json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner

DB_NAME = "nosql_labs"
COLLECTION = "backup_demo"
BACKUP_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")

SEED_DOCS = [
    {"order_id": f"ORD-{i:04d}", "customer": f"cust-{i % 20}", "amount": round(10 + i * 3.37, 2)}
    for i in range(500)
]


def tools_available() -> bool:
    return shutil.which("mongodump") is not None and shutil.which("mongorestore") is not None


def checksum_collection(col) -> str:
    """Deterministic checksum of a collection's contents, independent of
    insertion order or ObjectId (which mongorestore will regenerate)."""
    rows = []
    for doc in col.find({}, {"_id": 0}).sort([("order_id", 1)]):
        rows.append(json.dumps(doc, sort_keys=True))
    joined = "\n".join(rows)
    return hashlib.sha256(joined.encode()).hexdigest()


def run(cmd: list) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"    {result.stdout.strip().splitlines()[-1]}")
    if result.returncode != 0:
        print(f"    [ERROR] {result.stderr.strip()[-400:]}")
    return result


def main():
    banner("Lab 14.2: Automated Backup and Restore Verification")

    if not tools_available():
        print("  [ERROR] mongodump/mongorestore not found on PATH.")
        print("  Install the MongoDB Database Tools:")
        print("    https://www.mongodb.com/try/download/database-tools")
        print("  This lab cannot proceed without them -- stopping here.")
        return

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = os.path.join(BACKUP_ROOT, timestamp)
    os.makedirs(backup_dir, exist_ok=True)

    # --- Step 1: Seed known data and record its checksum ---
    print("=== Step 1: Seed collection and record baseline checksum ===")
    db = get_db(DB_NAME)
    col = reset_collection(DB_NAME, COLLECTION)
    col.insert_many(SEED_DOCS)
    original_count = col.count_documents({})
    original_checksum = checksum_collection(col)
    print(f"  [OK] Seeded {original_count} documents.")
    print(f"  Baseline checksum: {original_checksum[:16]}...")

    # --- Step 2: Back up with mongodump ---
    print(f"\n=== Step 2: Backup to {backup_dir} ===")
    dump_result = run([
        "mongodump",
        f"--uri={mongo_uri}",
        f"--db={DB_NAME}",
        f"--collection={COLLECTION}",
        f"--out={backup_dir}",
    ])
    if dump_result.returncode != 0:
        print("  [ERROR] mongodump failed -- stopping.")
        return
    print("  [OK] Backup complete.")

    # --- Step 3: Simulate data loss ---
    print("\n=== Step 3: Simulate data loss (drop the collection) ===")
    col.drop()
    lost_count = db[COLLECTION].count_documents({})
    print(f"  [OK] Collection dropped. Document count is now: {lost_count}")

    # --- Step 4: Restore from backup ---
    print("\n=== Step 4: Restore with mongorestore ===")
    dump_path = os.path.join(backup_dir, DB_NAME)
    restore_result = run([
        "mongorestore",
        f"--uri={mongo_uri}",
        f"--nsInclude={DB_NAME}.{COLLECTION}",
        dump_path,
    ])
    if restore_result.returncode != 0:
        print("  [ERROR] mongorestore failed -- stopping.")
        return

    # --- Step 5: Verify count AND content checksum ---
    print("\n=== Step 5: Verify restore integrity ===")
    restored_col = db[COLLECTION]
    restored_count = restored_col.count_documents({})
    restored_checksum = checksum_collection(restored_col)

    count_ok = restored_count == original_count
    checksum_ok = restored_checksum == original_checksum

    print(f"  Document count:  original={original_count}  restored={restored_count}  "
          f"{'[OK]' if count_ok else '[MISMATCH]'}")
    print(f"  Content checksum: {'MATCH' if checksum_ok else 'MISMATCH'} "
          f"({restored_checksum[:16]}...)")

    if count_ok and checksum_ok:
        print("\n  [OK] Restore verified: document count AND content checksum match.")
        print("  This backup is trustworthy for a real disaster-recovery drill.")
    else:
        print("\n  [FAIL] Restore does not match the original -- treat this backup")
        print("  as UNVERIFIED and investigate before relying on it.")

    print(f"\n  Backup retained at: {backup_dir}")
    print("  In production: run this exact verification (count + checksum, or a")
    print("  sampled document diff for large collections) automatically after")
    print("  every scheduled backup, and alert if verification fails -- a backup")
    print("  job that reports 'success' without verifying restorability is not")
    print("  a real recovery guarantee (this is the point Chapter 14 calls RPO/RTO).")

    banner("Lab 14.2 Complete")


if __name__ == "__main__":
    main()
