# Appendix A: Building and Deploying an LLM-Backed Chat Application on MongoDB

## What You'll Learn

- How every earlier chapter's concepts compose into one working system: MongoDB as the operational store, the vector store, and the conversation-memory store, all at once
- The full shape of a production RAG backend: document ingestion with chunking and embeddings, a chat endpoint that retrieves relevant context before calling an LLM, and a health check for orchestration
- Why a chat application needs its own persistence layer for conversation history, and why MongoDB (not just an in-memory list) is the right place for it
- How to containerize a multi-service application (backend + frontend + database) with Docker Compose so all three run and can reach each other with one command
- A subtle but critical containerization detail: why "localhost" means something different inside each container, and why that broke this exact application until it was fixed

## Prerequisites

MongoDB (local Docker or Atlas). Either an OpenAI API key or a locally running Ollama instance for the LLM backend. Docker and Docker Compose if you want to run the full containerized stack rather than each piece locally.

## Activity: Ingest Documents and Chat Against Them [`chat_api.py`, `streamlit_app.py`, `ingest_sample_data.py`]

### Topics You Need First

**This activity is where Chapters 2, 4-6, 12-14, and 17 all show up in one running system.** The backend uses PyMongo the same way Chapter 4 taught it; it stores conversation history in MongoDB the way Chapter 3 taught embedding vs. referencing (and this system chooses to store each message as its own document, referenced by session id -- consider why, versus embedding a growing messages array inside one session document); it builds a RAG pipeline directly extending Chapter 17's; and it gets deployed with the container patterns from Chapter 13.

**Ingestion: chunk, embed, store.** `POST /ingest` takes one or more documents, splits each into fixed-size word chunks (`chunk_size`, defaulting to 200 words), computes an embedding for each chunk, and stores every chunk as its own document with its embedding vector attached -- exactly the pipeline shape from Chapter 17's RAG activity, now wrapped in a real HTTP API.

**Chat: retrieve, then generate.** `POST /chat` embeds the incoming message, retrieves the `top_k` most similar chunks from MongoDB (via Atlas Vector Search if configured, or brute-force cosine similarity locally), constructs a prompt containing those chunks as context, and sends that prompt to whichever LLM backend is configured (OpenAI or a local Ollama model) -- then stores both the user's message and the assistant's response in the `sessions` collection before returning.

**Why conversation history lives in MongoDB, not in server memory.** An in-memory Python list of messages disappears the moment the backend process restarts, and doesn't work at all once you have more than one backend instance running behind a load balancer. Storing each message in MongoDB, tagged with a `session_id`, means conversations survive restarts and scale horizontally -- the same durability argument Chapter 10 made for transactions applies here to conversation state.

**Containerizing three services that need to reach each other.** The Docker Compose file defines `mongo`, `backend`, and `frontend` as separate services on the same Docker network, where each can reach the others by service name (`backend`, not `localhost`). This is the exact detail that broke the frontend originally: it defaulted to calling `http://localhost:8000`, which -- once containerized -- pointed the frontend container at *itself*, not at the backend container. The fix was making the backend URL configurable via a `BACKEND_URL` environment variable, set to `http://backend:8000` in the compose file.

### The Task

Populate the RAG database by running `ingest_sample_data.py` (or by making your own `POST /ingest` calls) against a running backend, then chat with it -- either through `streamlit_app.py`'s UI or by calling `POST /chat` directly -- and confirm the assistant's responses cite the sources it actually retrieved.

Before running the ingestion script: read `chat_api.py`'s `/ingest` endpoint and predict what would happen if you sent it multiple documents in a single request (this is the exact scenario a real bug in this codebase used to fail on, caused by a chunking loop variable that accidentally shadowed the chunking function's own name after the first document was processed -- fixed in the current version, but worth understanding *why* it would have broken, as a lesson in a very easy-to-make Python naming mistake).

## Files in This Directory

| File | Purpose |
|---|---|
| `chat_api.py` | FastAPI backend: `/ingest`, `/chat`, `/health` |
| `streamlit_app.py` | Chat UI frontend, talks to the backend over HTTP |
| `ingest_sample_data.py` | Populates the RAG database with sample textbook content |
| `Dockerfile` | Container build for the backend |
| `docker-compose.yml` | Full stack: MongoDB + backend + frontend, wired together on one Docker network |

## Check Your Work

Run `python ingest_sample_data.py` against a running backend and confirm it reports a non-zero `chunks_created` count for every sample document, not just the first one -- this specifically exercises the multi-document code path.

Then ask the chat interface a question whose answer clearly depends on the ingested content (not something the LLM would already know generically) and confirm the response's cited sources actually match content from your ingested documents, not empty or irrelevant ones -- that's your end-to-end proof that ingestion, embedding, retrieval, and generation are all correctly wired together.

If you run the full stack via `docker compose up`, confirm the frontend can actually reach the backend (the sidebar's health check should show "Backend: ..." rather than "Backend not reachable") -- if it can't, that's the `localhost`-vs-service-name issue described above resurfacing, and the fix is to make sure `BACKEND_URL` is set correctly for the frontend service in `docker-compose.yml`.
