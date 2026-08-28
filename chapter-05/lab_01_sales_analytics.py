"""Lab 5.1 - Build a Sales Analytics Pipeline

Multi-stage aggregation for revenue, top customers, order categorization.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from datetime import datetime
from rich.table import Table
from rich.console import Console

console = Console()

ORDERS = [
    {"order_id": "ORD-101", "customer": "Arjun", "status": "completed", "total": 2500, "items": 3, "date": "2024-01-15", "region": "North"},
    {"order_id": "ORD-102", "customer": "Sneha", "status": "completed", "total": 1800, "items": 1, "date": "2024-01-20", "region": "South"},
    {"order_id": "ORD-103", "customer": "Arjun", "status": "completed", "total": 3200, "items": 5, "date": "2024-02-01", "region": "North"},
    {"order_id": "ORD-104", "customer": "Kavya", "status": "cancelled", "total": 900, "items": 2, "date": "2024-02-05", "region": "East"},
    {"order_id": "ORD-105", "customer": "Rahul", "status": "completed", "total": 5600, "items": 8, "date": "2024-02-10", "region": "West"},
    {"order_id": "ORD-106", "customer": "Arjun", "status": "completed", "total": 1200, "items": 2, "date": "2024-02-15", "region": "North"},
    {"order_id": "ORD-107", "customer": "Sneha", "status": "completed", "total": 4100, "items": 6, "date": "2024-03-01", "region": "South"},
    {"order_id": "ORD-108", "customer": "Kavya", "status": "completed", "total": 2900, "items": 4, "date": "2024-03-05", "region": "East"},
    {"order_id": "ORD-109", "customer": "Rahul", "status": "pending", "total": 7800, "items": 10, "date": "2024-03-10", "region": "West"},
    {"order_id": "ORD-110", "customer": "Divya", "status": "completed", "total": 1500, "items": 1, "date": "2024-03-15", "region": "North"},
]


def main():
    banner("Lab 5.1: Sales Analytics Pipeline")
    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "orders")
    col.insert_many(ORDERS)
    print(f"[OK] Inserted {len(ORDERS)} orders.\n")

    # --- PIPELINE 1: Monthly Revenue ---
    print("=== Monthly Revenue (completed orders only) ===")
    pipeline_monthly = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": {"$substr": ["$date", 0, 7]},
            "total_revenue": {"$sum": "$total"},
            "order_count": {"$sum": 1},
            "avg_order_value": {"$avg": "$total"},
            "customers": {"$addToSet": "$customer"}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "month": "$_id",
            "total_revenue": 1,
            "order_count": 1,
            "avg_order_value": {"$round": ["$avg_order_value", 2]},
            "unique_customers": {"$size": "$customers"}
        }},
        {"$unset": "_id"},
    ]
    table = Table(title="Monthly Revenue Report")
    table.add_column("Month", style="cyan")
    table.add_column("Revenue", style="green", justify="right")
    table.add_column("Orders", justify="right")
    table.add_column("Avg Value", justify="right")
    table.add_column("Customers", justify="right")
    for row in col.aggregate(pipeline_monthly):
        table.add_row(
            row["month"], f"${row['total_revenue']:,.0f}",
            str(row["order_count"]), f"${row['avg_order_value']:,.2f}",
            str(row["unique_customers"])
        )
    console.print(table)

    # --- PIPELINE 2: Top 3 Customers ---
    print("\n=== Top 3 Customers by Total Spending ===")
    pipeline_top = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$customer",
            "total_spent": {"$sum": "$total"},
            "orders": {"$sum": 1},
            "items_bought": {"$sum": "$items"}
        }},
        {"$sort": {"total_spent": -1}},
        {"$limit": 3}
    ]
    for row in col.aggregate(pipeline_top):
        print(f"  {row['_id']:<12} ${row['total_spent']:>8,.0f} across {row['orders']} orders ({row['items_bought']} items)")

    # --- PIPELINE 3: Average Order Value by Status ---
    print("\n=== Avg Order Value by Status ===")
    pipeline_status = [
        {"$group": {
            "_id": "$status",
            "avg_value": {"$avg": "$total"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"avg_value": -1}}
    ]
    for row in col.aggregate(pipeline_status):
        print(f"  {row['_id']:<12} avg=${row['avg_value']:>8,.2f} ({row['count']} orders)")

    # --- PIPELINE 4: $bucket categorization ---
    print("\n=== Order Value Buckets ===")
    pipeline_bucket = [
        {"$bucket": {
            "groupBy": "$total",
            "boundaries": [0, 1000, 3000, 5000, 10000],
            "default": "Very High",
            "output": {"count": {"$sum": 1}, "total": {"$sum": "$total"}}
        }}
    ]
    labels = ["$0 - $1K", "$1K - $3K", "$3K - $5K", "$5K - $10K", "Very High"]
    for i, row in enumerate(col.aggregate(pipeline_bucket)):
        label = labels[i] if i < len(labels) else str(row["_id"])
        print(f"  {label:<15} {row['count']} orders, total=${row['total']:,.0f}")

    banner("Lab 5.1 Complete")


if __name__ == "__main__":
    main()