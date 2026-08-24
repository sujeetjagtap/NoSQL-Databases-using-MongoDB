"""Lab 12.1 (Python) - Field-Level Redaction via Views
Demonstrate creating a view that hides sensitive fields.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner

USERS = [
    {"username": "arjun", "email": "arjun@company.com", "role": "admin", "ssn": "111-22-3333", "salary": 150000},
    {"username": "sneha", "email": "sneha@company.com", "role": "developer", "ssn": "444-55-6666", "salary": 120000},
    {"username": "rahul", "email": "rahul@company.com", "role": "developer", "ssn": "777-88-9999", "salary": 130000},
]

def main():
    banner("Lab 12.1: Field-Level Redaction via Views")
    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "employees")
    col.insert_many(USERS)
    print("[OK] Inserted employee records.\n")

    # Full document (admin view)
    print("=== Full Document (Admin) ===")
    for doc in col.find({}, {"_id": 0}):
        print(f"  {doc}")

    # Create a redacted view
    pipeline = [{
        "$project": {
            "username": 1, "email": 1, "role": 1,
            "ssn": {"$concat": ["***-**-", {"$substr": ["$ssn", 8, 4]}]},
            "salary": "$$REMOVE"
        }
    }]
    db.command("create", "employees_safe", viewOn="employees", pipeline=pipeline)
    safe_view = db["employees_safe"]

    print("\n=== Redacted View (employees_safe) ===")
    for doc in safe_view.find({}, {"_id": 0}):
        print(f"  {doc}")

    print("\n  [NOTE] SSN is partially masked, salary is completely removed.")
    banner("Lab 12.1 Complete")


if __name__ == "__main__":
    main()
