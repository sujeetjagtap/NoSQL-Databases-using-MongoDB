"""Lab 15.2 - Data Migration Between Tenant Isolation Strategies

Lab 15.1 built a SaaS API using the "shared collection + tenant_id field"
isolation strategy (weakest isolation, simplest to run). A real product
often needs to move a specific tenant to a stronger isolation tier -- for
example, an enterprise customer who requires "database-per-tenant" for
compliance reasons, while smaller customers stay on the shared collection
to keep infrastructure costs down.

This lab migrates ONE tenant from the shared "saas_app.tasks" collection
(tenant_id field) into its own dedicated database (tenant_<id>.tasks),
with:
  - A dry-run mode that reports what WOULD move without writing anything.
  - An idempotent migration (safe to re-run; it upserts by task title
    rather than duplicating documents).
  - Post-migration verification (document count + content match).
  - A rollback path that deletes the tenant's dedicated database and
    leaves the shared collection untouched, in case anything looks wrong.
"""

import sys, os, argparse, hashlib, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, get_client, banner
from rich.table import Table
from rich.console import Console

console = Console()

SHARED_DB = "saas_app"
SHARED_COLLECTION = "tasks"


def seed_shared_data():
    """Recreate the Lab 15.1 shared-collection dataset for two tenants."""
    db = get_db(SHARED_DB)
    col = reset_collection(SHARED_DB, SHARED_COLLECTION)
    docs = [
        {"tenant_id": "tenant-acme", "title": "Setup ML Pipeline", "status": "open", "priority": "high"},
        {"tenant_id": "tenant-acme", "title": "Data Validation", "status": "open", "priority": "medium"},
        {"tenant_id": "tenant-globex", "title": "API Integration", "status": "open", "priority": "high"},
        {"tenant_id": "tenant-globex", "title": "User Testing", "status": "completed", "priority": "low"},
    ]
    col.insert_many(docs)
    return db, col


def tenant_db_name(tenant_id: str) -> str:
    return f"tenant_{tenant_id.replace('tenant-', '')}"


def content_checksum(docs: list) -> str:
    rows = [json.dumps(d, sort_keys=True) for d in sorted(docs, key=lambda d: d["title"])]
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def migrate_tenant(tenant_id: str, dry_run: bool = False) -> dict:
    """Migrate one tenant's documents from the shared collection to a
    dedicated database. Returns a summary dict for reporting."""
    client = get_client()
    shared_col = client[SHARED_DB][SHARED_COLLECTION]

    source_docs = list(shared_col.find({"tenant_id": tenant_id}, {"_id": 0}))
    if not source_docs:
        return {"tenant_id": tenant_id, "status": "NO_DATA", "moved": 0}

    if dry_run:
        return {
            "tenant_id": tenant_id,
            "status": "DRY_RUN",
            "would_move": len(source_docs),
            "target_db": tenant_db_name(tenant_id),
        }

    target_db_name = tenant_db_name(tenant_id)
    target_col = client[target_db_name][SHARED_COLLECTION]

    # Idempotent write: upsert on (tenant_id, title) so re-running the
    # migration never creates duplicates.
    moved = 0
    for doc in source_docs:
        target_col.update_one(
            {"tenant_id": doc["tenant_id"], "title": doc["title"]},
            {"$set": doc},
            upsert=True,
        )
        moved += 1

    # Verification: document count and content checksum must match.
    target_docs = list(target_col.find({}, {"_id": 0}))
    source_checksum = content_checksum(source_docs)
    target_checksum = content_checksum(target_docs)
    verified = (len(target_docs) == len(source_docs)) and (source_checksum == target_checksum)

    return {
        "tenant_id": tenant_id,
        "status": "MIGRATED" if verified else "VERIFICATION_FAILED",
        "moved": moved,
        "target_db": target_db_name,
        "source_count": len(source_docs),
        "target_count": len(target_docs),
        "verified": verified,
    }


def rollback_tenant(tenant_id: str):
    """Delete the tenant's dedicated database. The shared collection is
    never touched by migrate_tenant(), so rollback simply removes the copy."""
    client = get_client()
    target_db_name = tenant_db_name(tenant_id)
    client.drop_database(target_db_name)
    print(f"  [OK] Dropped database '{target_db_name}'. Shared collection is untouched.")


def print_summary(results: list):
    table = Table(title="Tenant Migration Summary")
    table.add_column("Tenant", style="cyan")
    table.add_column("Status")
    table.add_column("Target DB")
    table.add_column("Source Count", justify="right")
    table.add_column("Target Count", justify="right")
    for r in results:
        status_style = {
            "MIGRATED": "green", "DRY_RUN": "yellow",
            "VERIFICATION_FAILED": "bold red", "NO_DATA": "dim",
        }.get(r["status"], "")
        table.add_row(
            r["tenant_id"],
            f"[{status_style}]{r['status']}[/{status_style}]" if status_style else r["status"],
            r.get("target_db", "-"),
            str(r.get("source_count", r.get("would_move", "-"))),
            str(r.get("target_count", "-")),
        )
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Migrate a tenant to database-per-tenant isolation.")
    parser.add_argument("--tenant", default="tenant-acme", help="Tenant to migrate (default: tenant-acme)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would move without writing")
    parser.add_argument("--rollback", action="store_true", help="Undo a migration for --tenant")
    args = parser.parse_args()

    banner("Lab 15.2: Data Migration Between Tenant Isolation Strategies")

    print("=== Step 1: Seed shared-collection baseline (from Lab 15.1) ===")
    seed_shared_data()
    print(f"  [OK] Seeded shared collection '{SHARED_DB}.{SHARED_COLLECTION}' "
          f"for tenant-acme and tenant-globex.\n")

    if args.rollback:
        print(f"=== Rolling back migration for {args.tenant} ===")
        rollback_tenant(args.tenant)
        banner("Lab 15.2 Complete (rollback)")
        return

    print(f"=== Step 2: Migrate '{args.tenant}' "
          f"({'DRY RUN' if args.dry_run else 'LIVE'}) ===")
    result = migrate_tenant(args.tenant, dry_run=args.dry_run)
    print_summary([result])

    if not args.dry_run and result["status"] == "MIGRATED":
        print("\n=== Step 3: Re-run migration to prove it's idempotent ===")
        result2 = migrate_tenant(args.tenant, dry_run=False)
        print_summary([result2])
        if result2["target_count"] == result["target_count"]:
            print("  [OK] Re-running did not create duplicates -- migration is idempotent.")
        else:
            print("  [FAIL] Document count changed on re-run -- migration is NOT idempotent!")

        print(f"\n  Shared collection still has the original documents "
              f"(migration copies, it doesn't move-and-delete, until you")
        print(f"  explicitly clean up the source after confirming the new tier is stable).")
        print(f"\n  To undo this migration: "
              f"python chapter-15/lab_02_tenant_migration.py --tenant {args.tenant} --rollback")

    banner("Lab 15.2 Complete")


if __name__ == "__main__":
    main()
