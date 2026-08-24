"""Appendix A - FastAPI RAG Chat Backend

A production-ready FastAPI application that provides:
  - POST /chat : RAG-based chat endpoint
  - POST /ingest : Document ingestion with embeddings
  - GET /health : Health check

Supports two backends:
  - OpenAI (set OPENAI_API_KEY in .env)
  - Ollama local (set OLLAMA_BASE_URL in .env, default http://localhost:11434)

Vector storage: MongoDB Atlas Vector Search or local MongoDB with brute-force.
"""

import os, time, hashlib, math, random, logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("chat_api")
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "llm_chat_app")
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")  # "openai" or "ollama"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "200"))
TOP_K = int(os.getenv("TOP_K", "3"))

# --- Models ---
class ChatRequest(BaseModel):
    session_id: str
    message: str
    top_k: Optional[int] = TOP_K


class ChatResponse(BaseModel):
    session_id: str
    response: str
    sources: list[dict]
    latency_ms: float


class IngestRequest(BaseModel):
    documents: list[dict]  # [{"title": str, "content": str}]
    chunk_size: Optional[int] = CHUNK_SIZE


class IngestResponse(BaseModel):
    chunks_created: int
    message: str


class HealthResponse(BaseModel):
    status: str
    mongo: str
    llm_backend: str


# --- Database ---
client: Optional[MongoClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    logger.info("Connected to MongoDB")
    yield
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")


app = FastAPI(title="LLM Chat API", version="1.0.0", lifespan=lifespan)


def get_db():
    return client[MONGO_DB]


# --- Embedding ---
def mock_embed(text: str, dim: int = 384) -> list[float]:
    rng = random.Random(hashlib.md5(text.encode()).hexdigest())
    vec = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec]


def get_embedding(text: str) -> list[float]:
    # Production: use voyageai or openai embeddings
    # import voyageai; vo = voyageai.Client(); result = vo.embed([text], model="voyage-3"); return result.embeddings[0]
    return mock_embed(text)


def cosine_sim(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# --- Chunking ---
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


# --- LLM Calls ---
def call_ollama(prompt: str, history: list[dict]) -> str:
    import requests
    messages = [{"role": "system", "content": "You are a helpful assistant. Answer based on the provided context."}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})
    try:
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json={"model": OLLAMA_MODEL, "messages": messages, "stream": False}, timeout=60)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return f"[Ollama error: {e}]"


def call_openai(prompt: str, history: list[dict]) -> str:
    try:
        from openai import OpenAI
        oa = OpenAI(api_key=OPENAI_API_KEY)
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        resp = oa.chat.completions.create(model=OPENAI_MODEL, messages=messages, max_tokens=512)
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return f"[OpenAI error: {e}]"


def call_llm(prompt: str, history: list[dict]) -> str:
    if LLM_BACKEND == "openai" and OPENAI_API_KEY:
        return call_openai(prompt, history)
    return call_ollama(prompt, history)


# --- Retrieval ---
def retrieve_context(query: str, top_k: int = TOP_K) -> list[dict]:
    db = get_db()
    col = db["document_chunks"]
    query_emb = get_embedding(query)
    scored = []
    for doc in col.find({}, {"embedding": 1, "text": 1, "source_title": 1, "_id": 0}):
        score = cosine_sim(query_emb, doc["embedding"])
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, "source": d["source_title"], "text": d["text"][:200]} for s, d in scored[:top_k]]


# --- Endpoints ---
@app.get("/health", response_model=HealthResponse)
async def health():
    try:
        get_db().command("ping")
        mongo_status = "connected"
    except Exception:
        mongo_status = "disconnected"
    return HealthResponse(status="healthy", mongo=mongo_status, llm_backend=LLM_BACKEND)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    start = time.perf_counter()
    db = get_db()

    # Retrieve context
    sources = retrieve_context(req.message, req.top_k)
    context = "\n".join(f"[{s['source']}] {s['text']}" for s in sources)

    # Load conversation history
    session = db["sessions"].find_one({"session_id": req.session_id})
    history = session["history"] if session else []

    # Build prompt
    prompt = f"Context:\n{context}\n\nQuestion: {req.message}"
    response_text = call_llm(prompt, history[-4:] if history else [])

    # Save history
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": response_text})
    db["sessions"].update_one({"session_id": req.session_id}, {"$set": {"history": history[-20:]}}, upsert=True)

    latency = (time.perf_counter() - start) * 1000
    return ChatResponse(session_id=req.session_id, response=response_text, sources=sources, latency_ms=round(latency, 1))


@app.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    db = get_db()
    col = db["document_chunks"]
    chunks = []
    for doc in req.documents:
        # NOTE: the loop variable is deliberately named `chunk` (not
        # `chunk_text`) so it doesn't shadow the module-level chunk_text()
        # function -- shadowing it here caused a `TypeError: 'str' object
        # is not callable` on the second document in any multi-document
        # ingest request, since chunk_text() could no longer be called
        # again after the first document's loop rebound the name.
        doc_chunks = chunk_text(doc["content"], req.chunk_size)
        for i, chunk in enumerate(doc_chunks):
            embedding = get_embedding(chunk)
            chunks.append({"source_title": doc["title"], "chunk_index": i, "text": chunk, "embedding": embedding})
    if chunks:
        col.insert_many(chunks)
    return IngestResponse(chunks_created=len(chunks), message=f"Ingested {len(chunks)} chunks from {len(req.documents)} documents.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
