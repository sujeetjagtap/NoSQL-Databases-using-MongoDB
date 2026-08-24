"""Lab 16.1 - Model Data in Three Databases

Schema design and equivalent queries for MongoDB, Cassandra, Neo4j.
This is a comparison/script lab - run it to see all three schemas.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import banner
from rich.table import Table
from rich.console import Console

console = Console()


def show_mongodb_schema():
    print("=== MongoDB Schema (Document) ===")
    schema = """
  Collection: fraud_cases
  {
    "case_id": "FC-001",
    "suspect_id": "U-101",
    "amount": 50000,
    "currency": "INR",
    "merchant": "FakeStore",
    "timestamp": ISODate("2024-03-15T10:30:00Z"),
    "risk_score": 0.92,
    "tags": ["high-amount", "new-merchant", "off-hours"],
    "linked_accounts": ["U-102", "U-103"]
  }
"""
    print(schema)
    print("  Query (high-risk cases):")
    query = """
    db.fraud_cases.find({
      "risk_score": {"$gt": 0.8},
      "amount": {"$gt": 10000}
    }).sort({"timestamp": -1}).limit(10)
"""
    print(query)


def show_cassandra_schema():
    print("\n=== Cassandra Schema (Wide-Column) ===")
    schema = """
  CREATE TABLE fraud_events (
    case_id text,
    suspect_id text,
    amount decimal,
    merchant text,
    event_time timestamp,
    risk_score float,
    PRIMARY KEY ((suspect_id), event_time)
  ) WITH CLUSTERING ORDER BY (event_time DESC);

  INSERT INTO fraud_events (case_id, suspect_id, amount, merchant, event_time, risk_score)
    VALUES ('FC-001', 'U-101', 50000, 'FakeStore', '2024-03-15 10:30', 0.92);
"""
    print(schema)
    print("  Query (suspect recent fraud events):")
    query = """
    SELECT * FROM fraud_events
    WHERE suspect_id = 'U-101'
    LIMIT 10;
"""
    print(query)


def show_neo4j_schema():
    print("\n=== Neo4j Schema (Graph) ===")
    schema = """
  CREATE (u1:User {id: 'U-101', name: 'Arjun'})
  CREATE (u2:User {id: 'U-102', name: 'Sneha'})
  CREATE (u3:User {id: 'U-103', name: 'Rahul'})
  CREATE (m:Merchant {id: 'M-201', name: 'FakeStore'})
  CREATE (tx:Transaction {id: 'FC-001', amount: 50000, risk_score: 0.92})

  CREATE (u1)-[:MADE]->(tx)
  CREATE (m)-[:RECEIVED]->(tx)
  CREATE (u1)-[:SHARES_DEVICE_WITH]->(u2)
  CREATE (u2)-[:TRANSFERRED_TO]->(u3)
"""
    print(schema)
    print("  Query (fraud ring detection):")
    query = """
  MATCH path = (u1:User)-[:SHARES_DEVICE_WITH*1..3]-(u2:User)
  WHERE u1.id = 'U-101'
  RETURN path
"""
    print(query)


def comparison_table():
    print("\n=== Database Comparison for Fraud Detection ===")
    table = Table(show_lines=True)
    table.add_column("Aspect", style="cyan", width=22)
    table.add_column("MongoDB", width=28)
    table.add_column("Cassandra", width=28)
    table.add_column("Neo4j", width=28)
    table.add_row("Best For", "Flexible queries, ML pipeline", "Time-series events, writes", "Relationship traversal")
    table.add_row("Fraud Ring Query", "$graphLookup (limited)", "Not supported natively", "MATCH path (native)")
    table.add_row("Scalability", "Vertical + horizontal", "Linear horizontal", "Vertical (cluster)")
    table.add_row("Schema Flexibility", "High (dynamic)", "Requires predefined", "Nodes can vary")
    table.add_row("Data Model", "JSON documents", "Partitioned rows/cols", "Nodes + edges")
    console.print(table)


def main():
    banner("Lab 16.1: Polyglot Data Modeling")
    show_mongodb_schema()
    show_cassandra_schema()
    show_neo4j_schema()
    comparison_table()
    banner("Lab 16.1 Complete")


if __name__ == "__main__":
    main()