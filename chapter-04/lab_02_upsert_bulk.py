"""Lab 4.2 - Implement Upsert and Bulk Operations

Conditional inserts + batch modifications.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import UpdateOne
from config.connection import get_db, reset_collection, banner


SEED_PRODUCTS = [
    {"sku": "WGT-001", "name": "SmartWatch Pro", "price": 299.99, "stock": 50},
    {"sku": "WGT-002", "name": "FitBand Lite", "price": 49.99, "stock": 200},
]


def upsert_product(col, sku, update_fields):
    """Upsert a product by SKU. Creates if not exists, updates if it does."""
    result = col.update_one(
        {"sku": sku},
        {"$set": update_fields, "$setOnInsert": {"sku": sku}},
        upsert=True
    )
    action = "updated" if result.matched_count else "inserted"
    print(f"  [{action.upper()}] SKU={sku} (matched={result.matched_count}, upserted_id={'YES' if result.upserted_id else 'NO'})")
    return result


def main():
    banner("Lab 4.2: Upsert and Bulk Operations")
    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "inventory")
    col.insert_many(SEED_PRODUCTS)
    print(f"[OK] Seeded {len(SEED_PRODUCTS)} products.\n")

    # --- UPSERT DEMO ---
    print("=== Upsert: Existing SKU (should update) ===")
    upsert_product(col, "WGT-001", {"price": 279.99, "stock": 45})
    doc = col.find_one({"sku": "WGT-001"}, {"_id": 0})
    print(f"  Result: {doc}")

    print("\n=== Upsert: New SKU (should insert) ===")
    upsert_product(col, "WGT-003", {"name": "SmartRing X", "price": 199.99, "stock": 100})
    doc = col.find_one({"sku": "WGT-003"}, {"_id": 0})
    print(f"  Result: {doc}")

    # --- BULK WRITE DEMO ---
    print("\n=== Bulk Write: 5 operations in one call ===")
    operations = [
        UpdateOne({"sku": "WGT-001"}, {"$inc": {"stock": -10}}),              # Sold 10 units
        UpdateOne({"sku": "WGT-002"}, {"$mul": {"price": 0.9}}),                # 10% discount
        UpdateOne({"sku": "WGT-003"}, {"$set": {"active": True}}),               # Activate
        UpdateOne({"sku": "WGT-004"}, {"$set": {"name": "EarBuds Ultra", "price": 79.99, "stock": 150}}, upsert=True),  # Upsert
    ]
    bulk_result = col.bulk_write(operations)
    print(f"  Matched:      {bulk_result.matched_count}")
    print(f"  Modified:     {bulk_result.modified_count}")
    print(f"  Upserted:     {bulk_result.upserted_count}")
    print(f"  Inserted IDs: {bulk_result.upserted_ids}")

    # Final state
    print("\n=== Final Inventory State ===")
    for doc in col.find({}, {"_id": 0}).sort("sku"):
        print(f"  {doc.get('sku', 'N/A'):10} {doc.get('name', 'N/A'):<20} ${doc.get('price', 0):.2f}  stock={doc.get('stock', 'N/A')}")

    # --- IDEMPOTENCY DEMO: re-running the same bulk write ---
    print("\n=== Re-running the same bulk write (NOT all operations are idempotent) ===")
    bulk_result2 = col.bulk_write(operations)
    print(f"  Matched:      {bulk_result2.matched_count}")
    print(f"  Modified:     {bulk_result2.modified_count}")
    doc_004 = col.find_one({"sku": "WGT-001"}, {"_id": 0})
    print(f"  WGT-001 stock after 2nd run: {doc_004.get('stock')} "
          f"(dropped by another 10 -- $inc is NOT idempotent)")
    print("  $set operations (WGT-003's 'active' flag) ARE idempotent: setting")
    print("  the same value twice leaves the document unchanged either way.")
    print("  $inc and $mul are NOT idempotent: re-running the same bulk write")
    print("  changes the stock/price again each time it runs. This distinction")
    print("  matters for retry logic -- a network timeout that actually succeeded")
    print("  server-side, followed by a client retry, can silently double-apply")
    print("  a non-idempotent update.")

    banner("Lab 4.2 Complete")


if __name__ == "__main__":
    main()