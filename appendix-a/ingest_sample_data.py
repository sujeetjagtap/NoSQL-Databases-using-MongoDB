"""Appendix A - Ingest Sample Documents into the Chat App

Run this to populate the RAG database with textbook content for testing.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from config.connection import banner

BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

SAMPLE_DOCS = [
    {
        "title": "NoSQL Database Families",
        "content": (
            "NoSQL databases are categorized into four main families. "
            "Document databases like MongoDB store data as JSON-like documents with flexible schemas. "
            "Key-Value stores like Redis provide fast O(1) lookups for caching and session management. "
            "Wide-Column stores like Cassandra handle massive write throughput for time-series and IoT data. "
            "Graph databases like Neo4j model relationships between entities and excel at traversal queries."
        ),
    },
    {
        "title": "MongoDB CRUD Operations",
        "content": (
            "MongoDB provides a rich query language through Python's PyMongo driver. "
            "insert_one() and insert_many() create documents. find() retrieves with filters using "
            "comparison operators like $gt, $lt, $in, and logical operators like $or and $and. "
            "update_one() and update_many() modify documents using operators like $set, $inc, $push. "
            "delete_one() and delete_many() remove documents. All operations support projections to include or exclude fields."
        ),
    },
    {
        "title": "Aggregation Framework",
        "content": (
            "The MongoDB aggregation framework processes documents through a pipeline of stages. "
            "$match filters documents, $group aggregates them with functions like $sum, $avg, $max. "
            "$project reshapes documents, $unwind flattens arrays, $lookup performs joins across collections. "
            "$facet runs multiple sub-pipelines in parallel. For large results use allowDiskUse=True. "
            "The ESR rule (Equality, Sort, Range) guides compound index design for optimal performance."
        ),
    },
    {
        "title": "Replica Sets and Failover",
        "content": (
            "A MongoDB replica set provides high availability through data replication. "
            "One member is the primary (accepts writes) and others are secondaries (replicate data). "
            "If the primary fails, an election promotes a secondary. Write concern (w:1, w:majority) "
            "controls durability guarantees. Read preference (primary, secondary, nearest) controls read routing. "
            "For production, use w:majority with journaling for strong consistency."
        ),
    },
    {
        "title": "Vector Search and RAG",
        "content": (
            "MongoDB Atlas Vector Search enables semantic search using HNSW indexes on embedding vectors. "
            "Documents are embedded using models like OpenAI text-embedding-3 or Voyage AI. "
            "The $vectorSearch aggregation stage finds the top-k nearest neighbors. "
            "This enables RAG (Retrieval Augmented Generation) pipelines where relevant context is "
            "retrieved from MongoDB and passed to an LLM for grounded, accurate responses."
        ),
    },
]


def main():
    banner("Appendix A: Ingest Sample Documents")
    print(f"Sending {len(SAMPLE_DOCS)} documents to {BACKEND}/ingest...")

    try:
        resp = requests.post(
            f"{BACKEND}/ingest",
            json={"documents": SAMPLE_DOCS, "chunk_size": 50},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"[OK] {data['message']}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Backend not reachable. Start it first:")
        print("  cd appendix-a && uvicorn chat_api:app --reload")
    except Exception as e:
        print(f"[ERROR] {e}")

    banner("Ingest Complete")


if __name__ == "__main__":
    main()
