"""Lab 1.2 - Map a Real-World Application to NoSQL Families
Map data domains of real-world apps to appropriate NoSQL families."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console

console = Console()


def main():
    banner("Lab 1.2: Map Application Data Domains to NoSQL Families")

    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "app_domain_mapping")

    # --- Ride-Sharing Application ---
    print("=== Ride-Sharing Application ===")
    ride_sharing_domains = [
        {
            "app": "Ride-Sharing",
            "domain": "user_profiles",
            "description": "Rider and driver profiles with preferences, rating history, payment methods",
            "read_write_pattern": "Read-heavy, updated on each ride",
            "recommended_family": "Document",
            "recommended_db": "MongoDB",
            "rationale": "Nested structure (preferences, vehicles, payment methods) maps well to documents"
        },
        {
            "app": "Ride-Sharing",
            "domain": "ride_history",
            "description": "Completed ride records with route, fare, driver, passenger, timestamps",
            "read_write_pattern": "Write-heavy (append-only), range queries by date",
            "recommended_family": "Wide-Column",
            "recommended_db": "Apache Cassandra",
            "rationale": "High write throughput, time-range queries, horizontal scalability"
        },
        {
            "app": "Ride-Sharing",
            "domain": "real_time_tracking",
            "description": "Live GPS positions of active drivers, updated every 1-3 seconds",
            "read_write_pattern": "Extreme write + read, TTL-based expiry",
            "recommended_family": "Key-Value",
            "recommended_db": "Redis",
            "rationale": "Sub-millisecond reads, built-in TTL for stale positions, geospatial commands"
        },
        {
            "app": "Ride-Sharing",
            "domain": "payment_transactions",
            "description": "Payment records, refund logs, driver earnings, fare splits",
            "read_write_pattern": "Write-once, strong consistency required",
            "recommended_family": "Document",
            "recommended_db": "MongoDB (with ACID transactions)",
            "rationale": "Multi-document transactions for fare splits, flexible schema for varied payment types"
        },
    ]

    # --- Social Media Analytics Platform ---
    print("=== Social Media Analytics Platform ===")
    social_domains = [
        {
            "app": "Social Media Analytics",
            "domain": "content_feed",
            "description": "Posts, articles, media metadata with engagement metrics",
            "read_write_pattern": "Read-heavy, fan-out on write",
            "recommended_family": "Document",
            "recommended_db": "MongoDB",
            "rationale": "Flexible content schema, nested engagement counters, full-text search"
        },
        {
            "app": "Social Media Analytics",
            "domain": "social_graph",
            "description": "Follow/friend relationships, influence propagation, community detection",
            "read_write_pattern": "Traversals (multi-hop), relationship queries",
            "recommended_family": "Graph",
            "recommended_db": "Neo4j",
            "rationale": "Native graph traversals for friend-of-friend, shortest path, community detection"
        },
        {
            "app": "Social Media Analytics",
            "domain": "sentiment_timeseries",
            "description": "Hourly/daily sentiment scores per brand/topic, trend analysis",
            "read_write_pattern": "Time-series append, range scans, aggregation",
            "recommended_family": "Wide-Column",
            "recommended_db": "Apache Cassandra",
            "rationale": "Time-partitioned rows, high write throughput from streaming pipeline"
        },
        {
            "app": "Social Media Analytics",
            "domain": "media_assets",
            "description": "Images, videos, profile pictures stored as objects",
            "read_write_pattern": "Write-once, read-many, CDN delivery",
            "recommended_family": "Object/Key-Value",
            "recommended_db": "Amazon S3",
            "rationale": "Unlimited scalable object storage with CDN integration"
        },
    ]

    all_domains = ride_sharing_domains + social_domains
    col.insert_many(all_domains)
    print(f"[OK] Inserted {len(all_domains)} domain mappings.\n")

    # Print tables per application
    for app_name in ["Ride-Sharing", "Social Media Analytics"]:
        table = Table(title=f"{app_name} - Data Domain Mapping", show_lines=True)
        table.add_column("Domain", style="cyan", width=22)
        table.add_column("Description", width=55)
        table.add_column("NoSQL Family", style="magenta", width=16)
        table.add_column("Recommended DB", style="green", width=22)
        table.add_column("Key Rationale", width=48)

        for d in col.find({"app": app_name}):
            table.add_row(
                d["domain"], d["description"], d["recommended_family"],
                d["recommended_db"], d["rationale"]
            )
        console.print(table)
        print()

    # Summary: family distribution
    print("--- Family Distribution ---")
    pipeline = [
        {"$group": {"_id": "$recommended_family", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    for g in col.aggregate(pipeline):
        print(f"  {g['_id']:20} : {g['count']} domain(s)")

    banner("Lab 1.2 Complete")


if __name__ == "__main__":
    main()
