"""Lab 17.1 - Build a Simple RAG Pipeline

Chunk documents, generate embeddings (mock for local, real with VoyageAI),
vector search retrieval, LLM prompt construction, conversation memory.

For production: set VOYAGE_API_KEY and use Atlas Vector Search.
For local testing: this script uses mock embeddings and brute-force similarity.
"""

import sys, os, hashlib, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console

console = Console()


def mock_embed(text, dim=384):
    """Generate deterministic pseudo-random embedding for demo."""
    rng = random.Random(hashlib.md5(text.encode()).hexdigest())
    vec = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec]


def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    return sum(x * y for x, y in zip(a, b))


DOCUMENTS = [
    {
        "title": "Introduction to NoSQL",
        "content": (
            "NoSQL databases emerged in the late 2000s to address the limitations of "
            "traditional relational databases at web scale. Unlike RDBMS, NoSQL databases "
            "offer flexible schemas, horizontal scalability, and specialized data models. "
            "The four main families are Document (MongoDB, Couchbase), Key-Value (Redis, "
            "Memcached), Wide-Column (Cassandra, HBase), and Graph (Neo4j, Neptune). "
            "Each family is optimized for specific access patterns and use cases. "
            "Modern applications often use multiple NoSQL databases together in a "
            "polyglot persistence architecture, selecting the right tool for each data domain."
        ),
    },
    {
        "title": "MongoDB Aggregation Framework",
        "content": (
            "The MongoDB aggregation framework processes documents through a pipeline "
            "of stages. Each stage transforms the document stream: $match filters, "
            "$group aggregates, $project reshapes, $unwind denormalizes arrays, and "
            "$lookup performs left outer joins. The framework is powerful enough to "
            "replace complex SQL queries with subqueries and CTEs. For large datasets, "
            "use allowDiskUse=True to enable spill-to-disk. The $facet stage allows "
            "running multiple pipelines in parallel on the same input, useful for "
            "dashboard APIs that need different aggregations in one query."
        ),
    },
    {
        "title": "Vector Search and AI",
        "content": (
            "MongoDB Atlas Vector Search enables semantic search using vector embeddings. "
            "Documents are stored with an embedding field, and an HNSW index enables "
            "approximate nearest neighbor search. The $vectorSearch stage retrieves top-k "
            "most similar documents. This is the foundation for RAG pipelines, where "
            "relevant context is retrieved and passed to an LLM. Typical embedding models "
            "include OpenAI text-embedding-3-small and Voyage AI with 256 to 3072 dimensions."
        ),
    },
    {
        "title": "Replica Sets and High Availability",
        "content": (
            "A MongoDB replica set is a group of mongod instances that maintain the same "
            "data set. One member acts as the primary (receives writes), while others are "
            "secondaries (replicate from primary). If the primary fails, an election is held. "
            "Write concern controls how many nodes must acknowledge a write. Read preference "
            "controls which nodes serve reads. For production, use w:majority and read "
            "concern majority to prevent reading stale data after a failover."
        ),
    },
]

CHUNK_SIZE_WORDS = 50


def chunk_document(doc, chunk_size=CHUNK_SIZE_WORDS):
    """Split a document into word-based chunks."""
    words = doc["content"].split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk_text = " ".join(words[i : i + chunk_size])
        chunks.append({
            "source_title": doc["title"],
            "chunk_index": len(chunks),
            "text": chunk_text,
        })
    return chunks


class SimpleRAG:
    def __init__(self, db, collection_name="rag_documents"):
        self.col = reset_collection("nosql_labs", collection_name)
        self.db = db
        self.conversation_history = []

    def ingest(self, documents):
        """Chunk documents, embed, and store in MongoDB."""
        all_chunks = []
        for doc in documents:
            chunks = chunk_document(doc)
            for chunk in chunks:
                embedding = mock_embed(chunk["text"])
                all_chunks.append({**chunk, "embedding": embedding})
        if all_chunks:
            self.col.insert_many(all_chunks)
        print(f"  Ingested {len(all_chunks)} chunks from {len(documents)} documents.")

    def retrieve(self, query, top_k=3):
        """Find most similar chunks via brute-force cosine similarity."""
        query_embedding = mock_embed(query)
        scored = []
        for doc in self.col.find(
            {"embedding": 1, "text": 1, "source_title": 1, "chunk_index": 1, "_id": 0}
        ):
            score = cosine_similarity(query_embedding, doc["embedding"])
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]

    def build_prompt(self, query, context_chunks):
        """Construct an LLM prompt with retrieved context."""
        context = "\n".join(
            f"[{c['source_title']}] {c['text']}" for _, c in context_chunks
        )
        history_str = ""
        if self.conversation_history:
            history_str = "\nConversation History:\n"
            for turn in self.conversation_history[-4:]:
                history_str += f"  User: {turn['user']}\n  Assistant: {turn['assistant']}\n"
        prompt = (
            f"You are a helpful NoSQL/MongoDB tutor. Answer based on the context.\n\n"
            f"{history_str}\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\nAnswer:"
        )
        return prompt

    def chat(self, query, top_k=3):
        """Full RAG: retrieve -> build prompt -> (mock) generate."""
        print(f"\n  User: {query}")
        chunks = self.retrieve(query, top_k)
        prompt = self.build_prompt(query, chunks)

        # In production, send prompt to OpenAI/Ollama here
        mock_response = (
            f"[LLM would respond using {len(chunks)} retrieved chunks. "
            f"Prompt length: {len(prompt)} chars]"
        )
        self.conversation_history.append({"user": query, "assistant": mock_response})
        print(f"  Assistant: {mock_response}")

        print("  Sources:")
        table = Table()
        table.add_column("Score", justify="right", width=8)
        table.add_column("Source", style="cyan", width=30)
        table.add_column("Preview", width=50)
        for score, chunk in chunks:
            preview = chunk["text"][:50] + "..."
            table.add_row(f"{score:.4f}", chunk["source_title"], preview)
        console.print(table)


def main():
    banner("Lab 17.1: Build a Simple RAG Pipeline")
    db = get_db("nosql_labs")
    rag = SimpleRAG(db)

    print("=== Step 1: Ingest Documents ===")
    rag.ingest(DOCUMENTS)

    print("\n=== Step 2: Ask Questions (RAG) ===")
    questions = [
        "What are the four NoSQL database families?",
        "How does the aggregation framework pipeline work?",
        "What is HNSW and how is it used in MongoDB?",
        "How does replica set failover work?",
    ]
    for q in questions:
        rag.chat(q, top_k=2)

    print(f"\n  Conversation turns: {len(rag.conversation_history)}")
    banner("Lab 17.1 Complete")


if __name__ == "__main__":
    main()