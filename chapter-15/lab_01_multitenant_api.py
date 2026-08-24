"""Lab 15.1 - Design a Multi-Tenant APITask management SaaS with tenant isolation, CRUD, and rate limiting."""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console

console = Console()


def create_task(col, tenant_id, title, description, priority="medium", assignee=None):
    """Create a task with tenant isolation."""
    task = {
        "tenant_id": tenant_id,
        "title": title,
        "description": description,
        "priority": priority,
        "assignee": assignee,
        "status": "open",
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    result = col.insert_one(task)
    return str(result.inserted_id)


def get_tasks(col, tenant_id, status=None, priority=None):
    """Get tasks for a specific tenant with optional filters."""
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    return list(col.find(query, {"_id": 1, "title": 1, "status": 1, "priority": 1, "assignee": 1}))


def update_task(col, tenant_id, task_id, updates):
    """Update a task (tenant-scoped for safety)."""
    updates["updated_at"] = time.time()
    result = col.update_one(
        {"_id": task_id, "tenant_id": tenant_id},  # CRITICAL: tenant isolation
        {"$set": updates}
    )
    return result.modified_count > 0


def check_rate_limit(rate_col, tenant_id, limit=10, window_secs=60):
    """MongoDB-based rate limiter. Returns True if under limit."""
    cutoff = time.time() - window_secs
    count = rate_col.count_documents({
        "tenant_id": tenant_id,
        "timestamp": {"$gt": cutoff}
    })
    if count >= limit:
        return False
    rate_col.insert_one({"tenant_id": tenant_id, "timestamp": time.time()})
    return True


def main():
    banner("Lab 15.1: Multi-Tenant SaaS API")
    db = get_db("saas_app")
    tasks_col = reset_collection("saas_app", "tasks")
    rate_col = reset_collection("saas_app", "rate_limits")

    # Seed tasks for 2 tenants
    print("=== Creating Tasks ===")
    t1 = create_task(tasks_col, "tenant-acme", "Setup ML Pipeline", "Configure training pipeline for fraud model", "high", "arjun")
    t2 = create_task(tasks_col, "tenant-acme", "Data Validation", "Validate input data schema", "medium", "sneha")
    t3 = create_task(tasks_col, "tenant-globex", "API Integration", "Connect to payment gateway", "high", "rahul")
    t4 = create_task(tasks_col, "tenant-globex", "User Testing", "Run UAT for v2 release", "low")
    print(f"  Created 4 tasks across 2 tenants.")

    # List tasks per tenant (demonstrates isolation)
    for tenant in ["tenant-acme", "tenant-globex"]:
        print(f"\n=== {tenant} Tasks ===")
        tasks = get_tasks(tasks_col, tenant)
        for t in tasks:
            print(f"  [{t.get('priority','?'):6}] {t['title']:<30} ({t['status']}) -> {t.get('assignee','unassigned')}")

    # Update task (tenant-scoped)
    print("\n=== Update: Close ML Pipeline task ===")
    from bson import ObjectId
    success = update_task(tasks_col, "tenant-acme", ObjectId(t1), {"status": "completed"})
    print(f"  Update success: {success}")

    # Attempt cross-tenant access (should fail - no match)
    print("\n=== Cross-Tenant Access Attempt (should fail) ===")
    success = update_task(tasks_col, "tenant-globex", ObjectId(t1), {"status": "deleted"})
    print(f"  Globex trying to update Acme's task: {success} (False = blocked!)")

    # Rate limiting demo
    print("\n=== Rate Limiting (10 req/60s) ===")
    for i in range(12):
        allowed = check_rate_limit(rate_col, "tenant-acme", limit=10, window_secs=60)
        status = "ALLOWED" if allowed else "RATE LIMITED"
        print(f"  Request {i+1:2}: {status}")

    # Multi-tenant approaches table
    print("\n=== Multi-Tenant Architecture Comparison ===")
    table = Table(show_lines=True)
    table.add_column("Approach", style="cyan")
    table.add_column("Isolation", width=12)
    table.add_column("Pros", width=30)
    table.add_column("Cons", width=30)
    table.add_row("Collection-per-tenant", "Strong", "Simple RBAC, easy backup", "Many collections at scale")
    table.add_row("Document tenant_id", "Medium", "Single collection, flexible", "Query must include tenant_id")
    table.add_row("Database-per-tenant", "Strongest", "Full isolation", "Resource overhead, connection mgmt")
    console.print(table)

    banner("Lab 15.1 Complete")


if __name__ == "__main__":
    main()