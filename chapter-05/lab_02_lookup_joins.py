"""Lab 5.2 - Join Data with $lookup
Cross-collection joins, left joins, and pipeline sub-expressions.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner


ORDERS = [
    {"order_id": "ORD-201", "customer_id": "C001", "product_ids": ["P001", "P002"], "total": 350},
    {"order_id": "ORD-202", "customer_id": "C002", "product_ids": ["P003"], "total": 150},
    {"order_id": "ORD-203", "customer_id": "C003", "product_ids": ["P001", "P004", "P005"], "total": 680},
    {"order_id": "ORD-204", "customer_id": "C001", "product_ids": [], "total": 0},  # empty order
]

CUSTOMERS = [
    {"customer_id": "C001", "name": "Arjun", "tier": "Gold", "city": "Bangalore"},
    {"customer_id": "C002", "name": "Sneha", "tier": "Silver", "city": "Mumbai"},
    {"customer_id": "C003", "name": "Rahul", "tier": "Platinum", "city": "Delhi"},
]

PRODUCTS = [
    {"product_id": "P001", "name": "Widget A", "category": "Electronics", "price": 200},
    {"product_id": "P002", "name": "Gadget B", "category": "Accessories", "price": 150},
    {"product_id": "P003", "name": "Widget C", "category": "Electronics", "price": 150},
    {"product_id": "P004", "name": "Gadget D", "category": "Tools", "price": 280},
    {"product_id": "P005", "name": "Widget E", "category": "Consumables", "price": 200},
]


ndef main():
    banner("Lab 5.2: $lookup Joins")
    db = get_db("nosql_labs")
    orders_col = reset_collection("nosql_labs", "orders_join")
    customers_col = reset_collection("nosql_labs", "customers_join")
    products_col = reset_collection("nosql_labs", "products_join")

    orders_col.insert_many(ORDERS)
    customers_col.insert_many(CUSTOMERS)
    products_col.insert_many(PRODUCTS)
    print(f"[OK] Seeded orders ({len(ORDERS)}), customers ({len(CUSTOMERS)}), products ({len(PRODUCTS)}).")

    # --- BASIC $lookup: Orders + Customers ---
    print("\n=== 1. Orders with Customer Details ===")
    pipeline = [
        {"$lookup": {
            "from": "customers_join",
            "localField": "customer_id",
            "foreignField": "customer_id",
            "as": "customer"
        }},
        {"$unwind": "$customer"},
        {"$project": {
            "order_id": 1, "total": 1,
            "customer_name": "$customer.name",
            "customer_tier": "$customer.tier",
            "city": "$customer.city"
        }}
    ]
    for row in orders_col.aggregate(pipeline):
        print(f"  {row['order_id']:<10} {row['customer_name']:<10} [{row['customer_tier']}] ${row['total']}")

    # --- LEFT JOIN: Products never ordered ---
    print("\n=== 2. Products Never Ordered (Left Join + Empty Array Filter) ===")
    pipeline_never = [
        {"$lookup": {
            "from": "orders_join",
            "let": {"pid": "$product_id"},
            "pipeline": [
                {"$unwind": "$product_ids"},
                {"$match": {"$expr": {"$eq": ["$product_ids", "$$pid"]}}},
                {"$limit": 1}
            ],
            "as": "ordered"
        }},
        {"$match": {"ordered": {"$size": 0}}},
        {"$project": {"product_id": 1, "name": 1, "category": 1, "price": 1, "_id": 0}}
    ]
    never_ordered = list(products_col.aggregate(pipeline_never))
    if never_ordered:
        for p in never_ordered:
            print(f"  {p['product_id']:<8} {p['name']:<15} [{p['category']}] ${p['price']}")
    else:
        print("  All products have been ordered at least once.")

    # --- UNWIND + LOOKUP: Orders with Product Details ---
    print("\n=== 3. Order Line Items (Unwind products + $lookup) ===")
    pipeline_line = [
        {"$unwind": {"path": "$product_ids", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "products_join",
            "localField": "product_ids",
            "foreignField": "product_id",
            "as": "product_info"
        }},
        {"$unwind": {"path": "$product_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "order_id": 1,
            "product_id": "$product_ids",
            "product_name": "$product_info.name",
            "product_price": "$product_info.price"
        }}
    ]
    for row in orders_col.aggregate(pipeline_line):
        pname = row.get('product_name') or '(no product)'
        pprice = row.get('product_price') or 0
        print(f"  {row['order_id']:<10} -> {pname:<15} ${pprice}")

    banner("Lab 5.2 Complete")


if __name__ == "__main__":
    main()
