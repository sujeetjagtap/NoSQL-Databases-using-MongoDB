"""Lab 1.1 - Classify Database Products

NoSQL family identification and classification exercise.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner, print_json
from rich.table import Table
from rich.console import Console

console = Console()


def main():
    banner("Lab 1.1: Classify Database Products")

    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "database_products")

    # 10 real-world database products classified into NoSQL families
    products = [
        {"name": "Amazon S3", "family": "Document/Column", "data_model": "Object/Key-Value", "vendor": "AWS",
         "use_case": "Static asset storage, data lakes, backups", "open_source": False},
        {"name": "Couchbase", "family": "Document", "data_model": "JSON Document", "vendor": "Couchbase Inc.",
         "use_case": "Session management, caching layer, user profiles", "open_source": True},
        {"name": "Apache HBase", "family": "Wide-Column", "data_model": "Column-Family", "vendor": "Apache",
         "use_case": "Time-series, log aggregation, big data analytics", "open_source": True},
        {"name": "Amazon Neptune", "family": "Graph", "data_model": "Property Graph / RDF", "vendor": "AWS",
         "use_case": "Social networks, recommendation engines, fraud detection", "open_source": False},
        {"name": "Memcached", "family": "Key-Value", "data_model": "Key-Value (in-memory)", "vendor": "Open Source",
         "use_case": "Session caching, database query caching, page caching", "open_source": True},
        {"name": "Redis", "family": "Key-Value", "data_model": "Key-Value (in-memory, rich data types)", "vendor": "Redis Inc.",
         "use_case": "Caching, real-time leaderboards, pub/sub messaging", "open_source": True},
        {"name": "MongoDB", "family": "Document", "data_model": "BSON Document", "vendor": "MongoDB Inc.",
         "use_case": "Content management, IoT data, mobile backends, AI platforms", "open_source": True},
        {"name": "Apache Cassandra", "family": "Wide-Column", "data_model": "Column-Family (partitioned rows)", "vendor": "Apache",
         "use_case": "Time-series, messaging, global distribution at scale", "open_source": True},
        {"name": "Neo4j", "family": "Graph", "data_model": "Labeled Property Graph", "vendor": "Neo4j Inc.",
         "use_case": "Knowledge graphs, fraud rings, IT ops, recommendations", "open_source": True},
        {"name": "Elasticsearch", "family": "Search/Document", "data_model": "Inverted Index / JSON Document", "vendor": "Elastic",
         "use_case": "Full-text search, log analytics, observability", "open_source": True},
    ]

    col.insert_many(products)
    print(f"[OK] Inserted {len(products)} database products.\n")

    # Print a rich table
    table = Table(title="NoSQL Database Product Survey", show_lines=True)
    table.add_column("Product", style="cyan", width=16)
    table.add_column("Family", style="magenta", width=14)
    table.add_column("Data Model", width=30)
    table.add_column("Use Case", width=45)

    for p in col.find().sort("family"):
        table.add_row(p["name"], p["family"], p["data_model"], p["use_case"])

    console.print(table)

    # Group by family
    print("\n--- Grouped by Family ---")
    pipeline = [
        {"$group": {"_id": "$family", "count": {"$sum": 1}, "products": {"$push": "$name"}}},
        {"$sort": {"count": -1}}
    ]
    for group in col.aggregate(pipeline):
        print(f"  {group['_id']:12} : {group['count']} products -> {', '.join(group['products'])}")

    # Interactive: classify 3 mystery products
    print("\n--- Interactive Classification ---")
    print("Classify these 3 products into a NoSQL family:")
    mystery = [
        {"name": "DynamoDB", "hint": "AWS managed, single-digit ms latency, used for shopping carts"},
        {"name": "InfluxDB", "hint": "Purpose-built for time-series data, SQL-like query language"},
        {"name": "OrientDB", "hint": "Supports both document and graph models in one engine"},
    ]
    answers = {"DynamoDB": "Key-Value / Document", "InfluxDB": "Wide-Column / Time-Series", "OrientDB": "Multi-Model (Document + Graph)"}
    for m in mystery:
        print(f"  {m['name']}: {m['hint']}")
    print(f"\nExpected answers: {answers}")

    banner("Lab 1.1 Complete")


if __name__ == "__main__":
    main()
