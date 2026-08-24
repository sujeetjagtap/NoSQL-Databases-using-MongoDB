"""Lab 16.2 - Build a Hybrid Query Service

Lab 16.1 compared MongoDB, Cassandra, and Neo4j schemas side by side on
paper. This lab actually BUILDS a small hybrid query service that routes
each incoming query to the right engine based on its access pattern --
the real-world "polyglot persistence" pattern introduced in Chapter 16.

  - Entity lookups and attribute filters (e.g. "get case FC-001",
    "all high-risk cases") -> MongoDB. This is what document stores
    are good at.
  - Relationship/traversal queries (e.g. "who shares a device with
    U-101, up to 3 hops away") -> a graph engine. This is what graph
    databases are good at, and what MongoDB (a document store) is
    structurally NOT good at.

If a live Neo4j instance is reachable (NEO4J_URI set and the `neo4j`
driver installed), the graph queries run for real with Cypher. Otherwise
the service falls back to an in-memory adjacency-list graph and runs the
equivalent traversal in Python, so the routing logic and the lab are
still fully runnable without a Neo4j install -- with the fallback
clearly labeled so nobody mistakes it for a real Cypher benchmark.
"""

import sys, os
from collections import deque, defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console

console = Console()

CASES = [
    {"case_id": "FC-001", "suspect_id": "U-101", "amount": 50000, "risk_score": 0.92},
    {"case_id": "FC-002", "suspect_id": "U-102", "amount": 2200, "risk_score": 0.41},
    {"case_id": "FC-003", "suspect_id": "U-103", "amount": 71000, "risk_score": 0.88},
    {"case_id": "FC-004", "suspect_id": "U-104", "amount": 500, "risk_score": 0.12},
]

# device_id -> shares this device with these users (undirected graph edges)
DEVICE_LINKS = [
    ("U-101", "U-102", "DEV-500"),
    ("U-102", "U-103", "DEV-500"),
    ("U-103", "U-105", "DEV-777"),
    ("U-104", "U-106", "DEV-999"),
]


class InMemoryGraph:
    """A minimal undirected graph used as a fallback when Neo4j isn't
    available. Real Neo4j would run `MATCH path = (u1)-[:SHARES_DEVICE*1..N]-(u2)`;
    this does the same breadth-first traversal in Python."""

    def __init__(self):
        self.adjacency = defaultdict(set)

    def add_edge(self, a, b, label=""):
        self.adjacency[a].add((b, label))
        self.adjacency[b].add((a, label))

    def bfs_within_hops(self, start: str, max_hops: int) -> dict:
        """Return {node: hop_distance} for every node reachable from
        `start` within max_hops, excluding start itself."""
        visited = {start: 0}
        queue = deque([(start, 0)])
        while queue:
            node, dist = queue.popleft()
            if dist == max_hops:
                continue
            for neighbor, _label in self.adjacency[node]:
                if neighbor not in visited:
                    visited[neighbor] = dist + 1
                    queue.append((neighbor, dist + 1))
        visited.pop(start, None)
        return visited


def neo4j_available() -> bool:
    uri = os.getenv("NEO4J_URI")
    if not uri:
        return False
    try:
        import neo4j  # noqa: F401
        return True
    except ImportError:
        return False


class HybridQueryService:
    """Routes queries to MongoDB (documents/attributes) or a graph engine
    (relationships/traversal), matching the strengths of each database
    family discussed in Chapter 16."""

    def __init__(self, mongo_db):
        self.db = mongo_db
        self.cases_col = reset_collection("nosql_labs", "fraud_cases")
        self.cases_col.insert_many(CASES)

        self.use_real_neo4j = neo4j_available()
        if self.use_real_neo4j:
            from neo4j import GraphDatabase
            self.neo4j_driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "")),
            )
            self._seed_neo4j()
        else:
            self.graph = InMemoryGraph()
            for a, b, device in DEVICE_LINKS:
                self.graph.add_edge(a, b, device)

    def _seed_neo4j(self):
        with self.neo4j_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            for a, b, device in DEVICE_LINKS:
                session.run(
                    "MERGE (u1:User {id: $a}) MERGE (u2:User {id: $b}) "
                    "MERGE (u1)-[:SHARES_DEVICE {device: $device}]-(u2)",
                    a=a, b=b, device=device,
                )

    # --- Route 1: document / attribute queries -> MongoDB ---
    def get_case(self, case_id: str):
        """Point lookup by ID -- MongoDB's strength."""
        return self.cases_col.find_one({"case_id": case_id}, {"_id": 0})

    def high_risk_cases(self, threshold: float = 0.8):
        """Attribute range filter -- MongoDB's strength."""
        return list(self.cases_col.find({"risk_score": {"$gt": threshold}}, {"_id": 0}))

    # --- Route 2: relationship / traversal queries -> graph engine ---
    def find_linked_suspects(self, suspect_id: str, max_hops: int = 3) -> dict:
        """Multi-hop relationship traversal -- a graph engine's strength.
        MongoDB CAN do this with $graphLookup, but it gets expensive and
        awkward past 2-3 hops; a graph engine does it natively."""
        if self.use_real_neo4j:
            with self.neo4j_driver.session() as session:
                result = session.run(
                    f"MATCH path = (u1:User {{id: $id}})-[:SHARES_DEVICE*1..{max_hops}]-(u2:User) "
                    f"RETURN u2.id AS linked, length(path) AS hops",
                    id=suspect_id,
                )
                return {record["linked"]: record["hops"] for record in result}
        return self.graph.bfs_within_hops(suspect_id, max_hops)

    def close(self):
        if self.use_real_neo4j:
            self.neo4j_driver.close()


def main():
    banner("Lab 16.2: Build a Hybrid Query Service")

    db = get_db("nosql_labs")
    service = HybridQueryService(db)

    backend = "Neo4j (live)" if service.use_real_neo4j else "in-memory graph (Neo4j fallback)"
    print(f"  Graph backend in use: {backend}\n")

    print("=== Query 1 (routed to MongoDB): point lookup by case_id ===")
    case = service.get_case("FC-001")
    print(f"  {case}")

    print("\n=== Query 2 (routed to MongoDB): attribute filter, risk_score > 0.8 ===")
    high_risk = service.high_risk_cases(0.8)
    for c in high_risk:
        print(f"  {c}")

    print(f"\n=== Query 3 (routed to {backend.split(' ')[0]}): "
          f"who shares a device with U-101 within 3 hops? ===")
    linked = service.find_linked_suspects("U-101", max_hops=3)
    for user, hops in sorted(linked.items(), key=lambda kv: kv[1]):
        print(f"  {user}: {hops} hop(s) away")

    print("\n=== Routing Decision Table ===")
    table = Table(show_lines=True)
    table.add_column("Query Pattern", style="cyan", width=32)
    table.add_column("Routed To", width=14)
    table.add_column("Why", width=45)
    table.add_row("Get case by ID", "MongoDB", "Point lookup on an indexed field")
    table.add_row("Filter by risk_score range", "MongoDB", "Range query, native $gt/$lt support")
    table.add_row("Multi-hop relationship traversal", "Graph engine",
                  "Native pattern matching; MongoDB's $graphLookup works but "
                  "scales poorly past a few hops")
    console.print(table)

    service.close()
    banner("Lab 16.2 Complete")


if __name__ == "__main__":
    main()
