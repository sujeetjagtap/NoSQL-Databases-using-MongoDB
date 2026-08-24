"""Lab 18.2 - Write a Comparative Analysis Report

Synthesizes the fraud-detection capstone from Lab 18.1 into a structured,
shareable Markdown report -- the kind of document you would actually hand
to a team deciding which database(s) to run in production. The report
covers: Executive Summary, System Architecture, Query Performance
Comparison, Data Modeling Analysis, Scalability Assessment (1M / 10M /
100M transactions), and a Final Recommendation.

Where real numbers are available, this script measures them (it reuses
Lab 18.1's own MongoDB benchmark functions against a live database).
Where they are not (Cassandra and Neo4j are optional installs per the
README), it uses clearly labeled ESTIMATED figures based on each
database's well-documented architecture, rather than pretending to have
benchmarked engines it didn't actually run. Every estimated number is
marked as such directly in the report -- never mixed in silently with
measured ones.
"""

import sys, os, time, importlib.util
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import banner

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(THIS_DIR, "reports")


def load_lab_01():
    """Import Lab 18.1 as a module so we can reuse its data generator and
    MongoDB benchmark instead of duplicating that logic here."""
    path = os.path.join(THIS_DIR, "lab_01_comparative_capstone.py")
    spec = importlib.util.spec_from_file_location("lab_01_comparative_capstone", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_mongo_benchmark():
    """Try to run Lab 18.1's real MongoDB benchmark. Returns (results, measured:bool)."""
    try:
        lab01 = load_lab_01()
        from config.connection import get_db, reset_collection

        db = get_db("capstone")
        col = reset_collection("capstone", "transactions")
        txns = lab01.generate_transactions(n=10000, fraud_pct=200)
        col.insert_many(txns)
        col.create_index([("user_id", 1), ("timestamp", -1)], name="idx_user_time")
        col.create_index([("risk_score", -1)], name="idx_risk")
        col.create_index([("category", 1)], name="idx_category")
        results = lab01.benchmark_mongodb(col, txns)
        return results, True
    except Exception as e:
        print(f"  [WARN] Could not run a live MongoDB benchmark ({e}).")
        print("  Falling back to representative example figures for the report.")
        # Representative figures based on Lab 18.1's typical output shape,
        # clearly labeled ESTIMATED (not measured) in the generated report.
        return [
            ("Transaction History", 0.003, 50),
            ("High-Risk Query", 0.006, 200),
            ("Category Analytics", 0.011, 6),
            ("Write Throughput", 0.450, 1000),
        ], False


# Estimated (not measured -- see report note) Cassandra/Neo4j figures,
# based on documented architectural behavior rather than a live benchmark.
CASSANDRA_ESTIMATES = {
    "Transaction History": ("~2-5", "Partition-key lookup; very fast if user_id is the partition key"),
    "High-Risk Query": ("~50-200+", "Requires ALLOW FILTERING or a secondary index/materialized view; not a native fit"),
    "Category Analytics": ("N/A (needs Spark)", "Cassandra has no native aggregation framework"),
    "Write Throughput": ("Excellent (linear scale-out)", "Cassandra's core strength; adding nodes adds write capacity"),
}
NEO4J_ESTIMATES = {
    "Transaction History": ("~5-15", "Single relationship traversal from an indexed User node"),
    "High-Risk Query": ("~10-50", "Property filter on Transaction nodes; fine at moderate scale"),
    "Category Analytics": ("Weak fit", "Neo4j is not optimized for whole-graph aggregation"),
    "Write Throughput": ("Moderate", "Each write touches nodes + relationships + indexes; costlier than a document insert"),
}


def build_report(mongo_results, mongo_measured: bool) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("# Comparative Analysis Report: Fraud Detection Data Platform")
    lines.append(f"\n*Generated {generated_at} — Lab 18.2, based on the Lab 18.1 capstone dataset*\n")

    # --- Executive Summary ---
    lines.append("## Executive Summary\n")
    lines.append(
        "This report compares MongoDB, Cassandra, and Neo4j for a fraud-detection "
        "workload combining transaction history lookups, risk-score filtering, "
        "category analytics, and relationship-based fraud-ring detection. "
        "**No single database wins every query pattern.** The recommendation "
        "(see Final Recommendation) is a polyglot architecture: MongoDB as the "
        "operational store, with Neo4j added specifically for fraud-ring "
        "traversal once that becomes a first-class product requirement.\n"
    )

    # --- System Architecture ---
    lines.append("## System Architecture\n")
    lines.append("```")
    lines.append("            +-------------------+")
    lines.append("            |   Application /    |")
    lines.append("            |   Fraud Review UI  |")
    lines.append("            +----------+----------+")
    lines.append("                       |")
    lines.append("         +-------------+--------------+")
    lines.append("         |                             |")
    lines.append(" +-------v--------+           +--------v-------+")
    lines.append(" |    MongoDB     |           |     Neo4j      |")
    lines.append(" | (transactions, |           | (device/account|")
    lines.append(" |  risk scores,  |           |  relationship  |")
    lines.append(" |  analytics)    |           |  graph, fraud  |")
    lines.append(" |                |           |  ring queries) |")
    lines.append(" +----------------+           +----------------+")
    lines.append("")
    lines.append(" Cassandra: evaluated but NOT included in this architecture --")
    lines.append(" see Data Modeling Analysis for why.")
    lines.append("```\n")

    # --- Query Performance Comparison ---
    lines.append("## Query Performance Comparison\n")
    measured_note = (
        "*(MongoDB figures below were MEASURED against a live database.)*"
        if mongo_measured else
        "*(MongoDB figures below are ESTIMATED — no live database was reachable "
        "when this report was generated. Re-run with MongoDB running for real numbers.)*"
    )
    lines.append(measured_note + "\n")
    lines.append("| Query | MongoDB (ms) | Cassandra (ms, ESTIMATED) | Neo4j (ms, ESTIMATED) | Notes |")
    lines.append("|---|---|---|---|---|")
    for name, latency, _count in mongo_results:
        c_latency, c_note = CASSANDRA_ESTIMATES.get(name, ("?", ""))
        n_latency, n_note = NEO4J_ESTIMATES.get(name, ("?", ""))
        mongo_ms = f"{latency*1000:.1f}"
        lines.append(f"| {name} | {mongo_ms} | {c_latency} | {n_latency} | Cassandra: {c_note}. Neo4j: {n_note} |")
    lines.append("")

    # --- Data Modeling Analysis ---
    lines.append("## Data Modeling Analysis\n")
    lines.append(
        "- **MongoDB**: a single `transactions` document per event, with `user_id` "
        "and `risk_score` indexed, models this workload naturally and supports "
        "every query pattern except deep relationship traversal.\n"
        "- **Cassandra**: requires the query pattern to be known upfront and "
        "baked into the partition key (`PRIMARY KEY ((user_id), event_time)`). "
        "This makes the transaction-history query excellent but the ad-hoc "
        "risk-score filter and category analytics awkward or unsupported "
        "without a secondary system (Spark).\n"
        "- **Neo4j**: models users, merchants, and transactions as nodes with "
        "`SHARES_DEVICE`/`TRANSFERRED_TO` relationships. This is the only model "
        "of the three where 'find everyone within 3 hops of this suspect' is a "
        "native, efficient query rather than a workaround.\n"
    )

    # --- Scalability Assessment ---
    lines.append("## Scalability Assessment\n")
    lines.append("| Transactions | MongoDB | Cassandra | Neo4j |")
    lines.append("|---|---|---|---|")
    lines.append(
        "| 1M | Single replica set; comfortable on standard indexes | "
        "Comfortable on a small cluster | Comfortable on a single instance |"
    )
    lines.append(
        "| 10M | Sharding likely needed if write-heavy; read replicas help reads | "
        "Scales near-linearly by adding nodes | Fine for lookups; ring-detection "
        "queries start needing hop-limits |"
    )
    lines.append(
        "| 100M | Sharded cluster required; shard key choice (Ch. 11) becomes "
        "critical | Cassandra's strongest scale tier; this is its home turf | "
        "Needs careful relationship-density management and query hop-limits; "
        "consider Neo4j Fabric for sharding across a graph cluster |"
    )
    lines.append("")

    # --- Final Recommendation ---
    lines.append("## Final Recommendation\n")
    lines.append(
        "Start with **MongoDB alone** — it covers transaction storage, risk-score "
        "filtering, and category analytics well, and keeps operational complexity "
        "low (one database to run, back up, and secure; see Chapters 12–14). "
        "**Add Neo4j** only once fraud-ring / relationship detection becomes a "
        "product requirement that MongoDB's `$graphLookup` can no longer serve "
        "at acceptable latency (see Lab 16.2's hybrid routing pattern for how "
        "the two would coexist). **Cassandra is not recommended for this "
        "specific workload**: its write-throughput advantage doesn't offset "
        "the loss of ad-hoc querying and native aggregation that this fraud-review "
        "workload needs; it would be the right choice for a different workload "
        "(e.g. a pure high-volume event-ingestion pipeline with no complex "
        "read patterns).\n"
    )
    lines.append("---")
    lines.append(
        "*Cassandra and Neo4j figures in this report are architectural estimates, "
        "not measurements from a live benchmark. To replace them with real numbers, "
        "provision a Cassandra and/or Neo4j instance and extend this script's "
        "`get_mongo_benchmark()` pattern with equivalent `get_cassandra_benchmark()` "
        "/ `get_neo4j_benchmark()` functions.*"
    )

    return "\n".join(lines)


def main():
    banner("Lab 18.2: Write a Comparative Analysis Report")

    print("=== Step 1: Gather MongoDB performance numbers ===")
    mongo_results, measured = get_mongo_benchmark()
    if measured:
        print("  [OK] Live MongoDB benchmark complete.")
    else:
        print("  [OK] Using representative example figures (see report note).")

    print("\n=== Step 2: Build the report ===")
    report_md = build_report(mongo_results, measured)

    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = os.path.join(REPORT_DIR, f"comparative_analysis_{timestamp}.md")
    with open(report_path, "w") as f:
        f.write(report_md)

    print(f"  [OK] Report written to: {report_path}")
    print(f"  Sections: Executive Summary, System Architecture, Query Performance "
          f"Comparison, Data Modeling Analysis, Scalability Assessment, "
          f"Final Recommendation.")

    print("\n  Try it yourself: extend get_mongo_benchmark()'s pattern to add real")
    print("  Cassandra and Neo4j benchmarks if you have those databases available,")
    print("  and compare your measured numbers against this report's estimates.")

    banner("Lab 18.2 Complete")


if __name__ == "__main__":
    main()
