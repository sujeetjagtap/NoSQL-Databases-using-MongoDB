"""Lab 18.1 - Comparative Capstone Lab

Build a fraud detection benchmark across MongoDB, Cassandra, and Neo4j.
This script handles the MongoDB portion and provides benchmarking infrastructure.
Cassandra and Neo4j scripts are provided separately for when those databases are available.

The lab generates synthetic transaction data, inserts into MongoDB, runs 4 benchmark
queries, measures latency, and produces a comparison report.
"""

import sys, os, time, random, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console
from datetime import datetime, timedelta

console = Console()

NUM_TRANSACTIONS = 10000
NUM_FRAUD = 200


def generate_transactions(n=NUM_TRANSACTIONS, fraud_pct=NUM_FRAUD):
    """Generate synthetic financial transactions."""
    users = [f"U-{i:04d}" for i in range(1, 501)]
    merchants = [f"M-{i:04d}" for i in range(1, 101)]
    categories = ["electronics", "groceries", "travel", "dining", "fashion", "utilities"]
    locations = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune"]

    txns = []
    for i in range(n):
        is_fraud = i < fraud_pct
        txn = {
            "txn_id": f"TXN-{i:06d}",
            "user_id": random.choice(users),
            "merchant_id": random.choice(merchants),
            "category": random.choice(categories),
            "location": random.choice(locations),
            "amount": round(random.uniform(10, 5000), 2),
            "timestamp": (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 180))).isoformat(),
            "is_fraud": is_fraud,
            "risk_score": round(random.uniform(0.7, 1.0), 4) if is_fraud else round(random.uniform(0.0, 0.5), 4),
            "device_id": f"DEV-{random.randint(1, 200):04d}",
        }
        txns.append(txn)
    return txns


def benchmark_mongodb(col, txns):
    """Run all 4 benchmark queries on MongoDB and measure latency."""
    results = []

    # Q1: Transaction history for a user (point lookup + sort)
    print("  Q1: Transaction history for user U-0001 (sorted by timestamp)...")
    start = time.perf_counter()
    q1_result = list(col.find({"user_id": "U-0001"}).sort("timestamp", -1).limit(50))
    t1 = time.perf_counter() - start
    results.append(("Transaction History", t1, len(q1_result)))
    print(f"      {len(q1_result)} docs in {t1*1000:.1f} ms")

    # Q2: High-risk transactions (range query)
    print("  Q2: High-risk transactions (risk_score > 0.8)...")
    start = time.perf_counter()
    q2_result = list(col.find({"risk_score": {"$gt": 0.8}}, {"_id": 0, "txn_id": 1, "risk_score": 1, "amount": 1}))
    t2 = time.perf_counter() - start
    results.append(("High-Risk Query", t2, len(q2_result)))
    print(f"      {len(q2_result)} docs in {t2*1000:.1f} ms")

    # Q3: Analytics - spending by category
    print("  Q3: Spending by category (aggregation)...")
    start = time.perf_counter()
    q3_pipeline = [
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]
    q3_result = list(col.aggregate(q3_pipeline))
    t3 = time.perf_counter() - start
    results.append(("Category Analytics", t3, len(q3_result)))
    print(f"      {len(q3_result)} categories in {t3*1000:.1f} ms")

    # Q4: Write throughput - insert 1000 docs
    print("  Q4: Write throughput (1,000 inserts)...")
    extra = [{"txn_id": f"BENCH-{i}", "user_id": "U-0001", "amount": 100, "timestamp": datetime.now().isoformat(), "is_fraud": False, "risk_score": 0.1, "merchant_id": "M-0001", "category": "test", "location": "test", "device_id": "DEV-0001"} for i in range(1000)]
    start = time.perf_counter()
    col.insert_many(extra)
    t4 = time.perf_counter() - start
    results.append(("Write Throughput", t4, 1000))
    print(f"      1,000 inserts in {t4*1000:.1f} ms ({1000/t4:,.0f} ops/sec)")

    return results


def cassandra_queries_script():
    """Return CQL equivalent scripts for reference."""
    return """
    -- Q1: Transaction history (requires partition key = user_id)
    SELECT * FROM transactions WHERE user_id = 'U-0001' LIMIT 50;

    -- Q2: High-risk (requires secondary index or materialized view)
    CREATE INDEX idx_risk ON transactions(risk_score);
    SELECT * FROM transactions WHERE risk_score > 0.8 ALLOW FILTERING;

    -- Q3: Analytics (Cassandra is NOT good at this - requires Spark)
    -- Use Spark Cassandra Connector for aggregation

    -- Q4: Write throughput
    -- Cassandra excels here: linear write scaling
    """


def neo4j_queries_script():
    """Return Cypher equivalent scripts for reference."""
    return """
    // Q1: Transaction history
    MATCH (u:User {id: 'U-0001'})-[:MADE]->(t:Transaction)
    RETURN t ORDER BY t.timestamp DESC LIMIT 50;

    // Q2: Fraud ring detection (graph's strength!)
    MATCH path = (u1:User)-[:SHARES_DEVICE*1..3]-(u2:User)
    WHERE u1.id = 'U-0001'
    WITH u1, u2, COUNT(*) AS shared_signals
    WHERE shared_signals >= 2
    RETURN u1.id, u2.id, shared_signals
    ORDER BY shared_signals DESC;

    // Q3: Category analytics (not Neo4j's strength)
    MATCH (t:Transaction)
    WITH t.category AS cat, SUM(t.amount) AS total, COUNT(t) AS cnt
    RETURN cat, total, cnt ORDER BY total DESC;

    // Q4: Write throughput (graph writes are expensive)
    """


def print_report(mongo_results):
    """Print final comparison report."""
    print("\n" + "=" * 80)
    print("  COMPARATIVE CAPSTONE REPORT")
    print("=" * 80)

    table = Table(title="MongoDB Benchmark Results")
    table.add_column("Query", style="cyan", width=25)
    table.add_column("Latency (ms)", justify="right", width=15)
    table.add_column("Result Count", justify="right", width=15)
    table.add_column("Strength", style="green", width=25)

    strengths = [
        "Flexible schema, good latency",
        "$gt index scan, expressive",
        "Native aggregation pipeline",
        "Good write throughput",
    ]
    for (name, latency, count), strength in zip(mongo_results, strengths):
        table.add_row(name, f"{latency*1000:.1f}", str(count), strength)
    console.print(table)

    print("\n  Cassandra Equivalents:")
    print(cassandra_queries_script())

    print("  Neo4j Equivalents:")
    print(neo4j_queries_script())

    print("\n  Key Insight: Each database excels at different query patterns.")
    print("  MongoDB = flexible queries + aggregation")
    print("  Cassandra = high-throughput writes + time-series reads")
    print("  Neo4j   = relationship traversal + fraud ring detection")


def main():
    banner("Lab 18.1: Comparative Capstone - Fraud Detection")
    db = get_db("capstone")
    col = reset_collection("capstone", "transactions")

    # Generate and insert data
    print(f"Generating {NUM_TRANSACTIONS:,} synthetic transactions...")
    txns = generate_transactions()
    start = time.perf_counter()
    col.insert_many(txns)
    load_time = time.perf_counter() - start
    print(f"[OK] Inserted {NUM_TRANSACTIONS:,} transactions in {load_time:.2f}s ({NUM_TRANSACTIONS/load_time:,.0f} docs/sec)")

    # Create indexes for fair benchmark
    print("Creating indexes...")
    col.create_index([("user_id", 1), ("timestamp", -1)], name="idx_user_time")
    col.create_index([("risk_score", -1)], name="idx_risk")
    col.create_index([("category", 1)], name="idx_category")

    # Run benchmarks
    print("\n=== Running Benchmark Queries ===")
    results = benchmark_mongodb(col, txns)
    print_report(results)

    banner("Lab 18.1 Complete")


if __name__ == "__main__":
    main()
