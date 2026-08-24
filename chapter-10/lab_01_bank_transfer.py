"""Lab 10.1 - Implement a Bank Transfer Transaction
Multi-document ACID transactions with retry logic.

Requires: MongoDB 4.0+ with WiredTiger (default in v7)
For multi-document transactions on standalone: enable --replSet (even single-node)
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient, WriteConcern
from pymongo.errors import OperationFailure
from config.connection import banner

URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MAX_RETRIES = 3
RETRY_DELAY_MS = 100


def create_accounts(col):
    """Seed accounts collection with test data."""
    col.drop()
    col.insert_many([
        {"account_id": "ACC-001", "holder": "Arjun", "balance": 5000.00},
        {"account_id": "ACC-002", "holder": "Sneha", "balance": 3000.00},
        {"account_id": "ACC-003", "holder": "Rahul", "balance": 1000.00},
    ])
    print("  [OK] Created 3 accounts.")


def transfer_funds(col, from_id, to_id, amount, description):
    """Transfer funds between accounts using ACID transaction.
    Returns True on success, raises on failure.
    """
    client = col.database.client
    session = client.start_session()
    
    try:
        with session.start_transaction(
            read_concern={"level": "snapshot"},
            write_concern=WriteConcern(w="majority")
        ):
            # Debit sender
            debit_result = col.update_one(
                {"account_id": from_id, "balance": {"$gte": amount}},
                {"$inc": {"balance": -amount}},
                session=session
            )
            if debit_result.matched_count == 0:
                raise ValueError(f"Insufficient funds in {from_id} (need {amount})")

            # Credit receiver
            col.update_one(
                {"account_id": to_id},
                {"$inc": {"balance": amount}},
                session=session
            )

            # Record transaction
            col.database["transactions"].insert_one({
                "from": from_id, "to": to_id, "amount": amount,
                "description": description, "timestamp": time.time()
            }, session=session)

        print(f"  [OK] Transferred {amount} from {from_id} -> {to_id}")
        return True

    except (OperationFailure, ValueError) as e:
        print(f"  [ROLLBACK] Transfer failed: {e}")
        session.abort_transaction()
        return False
    finally:
        session.end_session()


def print_balances(col):
    """Print all account balances."""
    print("  Current Balances:")
    for doc in col.find({}, sort=[("account_id", 1)]):
        print(f"    {doc['account_id']}: {doc['holder']:<12} ${doc['balance']:>10,.2f}")


def main():
    banner("Lab 10.1: Bank Transfer Transaction")
    client = MongoClient(URI, serverSelectionTimeoutMS=5000)
    db = client["bank"]
    col = db["accounts"]

    create_accounts(col)
    print_balances(col)

    # Scenario 1: Successful transfer
    print("\n=== Transfer $1500: ACC-001 -> ACC-002 ===")
    transfer_funds(col, "ACC-001", "ACC-002", 1500, "Salary payment")
    print_balances(col)

    # Scenario 2: Insufficient funds (should rollback)
    print("\n=== Transfer $5000: ACC-003 -> ACC-001 (insufficient) ===")
    transfer_funds(col, "ACC-003", "ACC-001", 5000, "Should fail")
    print_balances(col)

    # Scenario 3: Retry logic demonstration
    print("\n=== Transfer with Retry Logic ===")
    for attempt in range(1, MAX_RETRIES + 1):
        if transfer_funds(col, "ACC-002", "ACC-003", 500, f"Retry attempt {attempt}"):
            break
        time.sleep(RETRY_DELAY_MS / 1000)
    print_balances(col)

    # Show transaction log
    print("\n=== Transaction Log ===")
    for t in db["transactions"].find({}, {"_id": 0}).sort("timestamp", 1):
        print(f"  {t['from']} -> {t['to']}: ${t['amount']} ({t['description']})")

    client.close()
    banner("Lab 10.1 Complete")


if __name__ == "__main__":
    main()