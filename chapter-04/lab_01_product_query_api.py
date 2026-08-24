"""Lab 4.1 - Build a Product Query API
Full CRUD with comparison, logical, array operators, projections, pagination.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console

console = Console()

# Sample products
PRODUCTS = [
    {"sku": "LAP-001", "name": "ProBook 15", "category": "Laptops", "price": 899.99,
     "brand": "TechCorp", "stock": 45, "tags": ["business", "15-inch"],
     "specifications": {"cpu": "i7-13700H", "ram": "16GB", "ssd": "512GB"},
     "rating": 4.5, "active": True},
    {"sku": "LAP-002", "name": "UltraBook 14", "category": "Laptops", "price": 1299.99,
     "brand": "TechCorp", "stock": 12, "tags": ["premium", "14-inch", "lightweight"],
     "specifications": {"cpu": "i9-13900H", "ram": "32GB", "ssd": "1TB"},
     "rating": 4.8, "active": True},
    {"sku": "MON-001", "name": "WideView 27", "category": "Monitors", "price": 449.99,
     "brand": "DisplayPlus", "stock": 30, "tags": ["4K", "27-inch", "USB-C"],
     "specifications": {"resolution": "3840x2160", "panel": "IPS", "refresh": "60Hz"},
     "rating": 4.3, "active": True},
    {"sku": "MON-002", "name": "GamePanel 32", "category": "Monitors", "price": 699.99,
     "brand": "DisplayPlus", "stock": 8, "tags": ["gaming", "32-inch", "144Hz"],
     "specifications": {"resolution": "2560x1440", "panel": "VA", "refresh": "144Hz"},
     "rating": 4.7, "active": True},
    {"sku": "KBD-001", "name": "TypeMaster Pro", "category": "Keyboards", "price": 149.99,
     "brand": "KeyTech", "stock": 100, "tags": ["mechanical", "wireless", "backlit"],
     "specifications": {"switch": "Cherry MX Brown", "layout": "Full-Size", "battery": "200h"},
     "rating": 4.6, "active": True},
    {"sku": "KBD-002", "name": "SilentType 60", "category": "Keyboards", "price": 89.99,
     "brand": "KeyTech", "stock": 0, "tags": ["mechanical", "60-percent", "silent"],
     "specifications": {"switch": "Cherry MX Silent Red", "layout": "60%", "battery": "150h"},
     "rating": 4.4, "active": False},
    {"sku": "LAP-003", "name": "BudgetBook 15", "category": "Laptops", "price": 549.99,
     "brand": "ValueTech", "stock": 0, "tags": ["budget", "15-inch"],
     "specifications": {"cpu": "i5-1335U", "ram": "8GB", "ssd": "256GB"},
     "rating": 3.9, "active": False},
]


def search_products(col, query_filter, projection=None, sort_key=None, sort_dir=1, page=1, page_size=3):
    """Generic paginated search function."""
    skip = (page - 1) * page_size
    cursor = col.find(query_filter, projection)
    if sort_key:
        cursor = cursor.sort(sort_key, sort_dir)
    total = col.count_documents(query_filter)
    results = list(cursor.skip(skip).limit(page_size))
    return results, total


def main():
    banner("Lab 4.1: Product Query API")
    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "products")
    col.insert_many(PRODUCTS)
    print(f"[OK] Inserted {len(PRODUCTS)} products.\n")

    # 1. Comparison operators
    print("=== Comparison: Price $gte 500, $lte 800 ===")
    results = col.find({"price": {"$gte": 500, "$lte": 800}}, {"name": 1, "price": 1, "_id": 0})
    for r in results:
        print(f"  {r['name']:<20} ${r['price']:.2f}")

    # 2. Logical operators
    print("\n=== Logical: Laptops OR Monitors, price > 600 ===")
    results = col.find({
        "$or": [
            {"category": "Laptops"},
            {"category": "Monitors"}
        ],
        "price": {"$gt": 600}
    }, {"name": 1, "category": 1, "price": 1, "_id": 0})
    for r in results:
        print(f"  {r['name']:<20} [{r['category']}] ${r['price']:.2f}")

    # 3. Array operators
    print("\n=== Array: Products tagged 'mechanical' ===")
    results = col.find({"tags": "mechanical"}, {"name": 1, "tags": 1, "_id": 0})
    for r in results:
        print(f"  {r['name']:<20} tags: {r['tags']}")

    print("\n=== $elemMatch: Stock > 10 AND rating >= 4.5 ===")
    results = col.find({
        "stock": {"$gt": 10},
        "rating": {"$gte": 4.5}
    }, {"name": 1, "stock": 1, "rating": 1, "_id": 0})
    for r in results:
        print(f"  {r['name']:<20} stock={r['stock']} rating={r['rating']}")

    # 4. Projection
    print("\n=== Projection: Name + CPU only (Laptops) ===")
    results = col.find(
        {"category": "Laptops"},
        {"name": 1, "specifications.cpu": 1, "_id": 0}
    )
    for r in results:
        print(f"  {r['name']:<20} CPU: {r['specifications']['cpu']}")

    # 5. Pagination
    print("\n=== Pagination: Page 1, size=3 ===")
    page_results, total = search_products(col, {"active": True}, page=1, page_size=3)
    for r in page_results:
        print(f"  {r['name']:<20} ${r['price']:.2f}")
    print(f"  Showing 3 of {total} active products")

    print("\n=== Pagination: Page 2, size=3 ===")
    page_results, _ = search_products(col, {"active": True}, page=2, page_size=3)
    for r in page_results:
        print(f"  {r['name']:<20} ${r['price']:.2f}")

    # 6. $all - products with ALL specified tags
    print("\n=== $all: Products tagged BOTH 'mechanical' AND 'wireless' ===")
    results = col.find({"tags": {"$all": ["mechanical", "wireless"]}}, {"name": 1, "tags": 1, "_id": 0})
    for r in results:
        print(f"  {r['name']:<20} {r['tags']}")

    # 7. $ne - exclude
    print("\n=== $ne: Products NOT from KeyTech ===")
    results = col.find({"brand": {"$ne": "KeyTech"}}, {"name": 1, "brand": 1, "_id": 0})
    for r in results:
        print(f"  {r['name']:<20} by {r['brand']}")

    banner("Lab 4.1 Complete")


if __name__ == "__main__":
    main()