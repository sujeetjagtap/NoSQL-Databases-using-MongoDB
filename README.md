# NoSQL Databases using MongoDB Textbook - Lab Scripts

Complete Python, Shell, and infrastructure scripts for all 36 hands-on labs
(2 per chapter x 18 chapters) plus the Appendix A capstone, from the
textbook *"NoSQL Databases Using MongoDB: A Practical Guide to NoSQL Concepts, Data Modeling, and Real-world Applications with MongoDB"*.

https://www.lurnexa.in/textbooks/nosql-databases-using-mongodb/

---

## Quick Start

```bash
# 1. Clone and install dependencies
pip install -r requirements.txt

# 2. Start MongoDB (Docker, one-liner)
docker run -d -p 27017:27017 --name mongo mongo:7

# 3. Copy and edit environment
cp .env.example .env
# Edit .env with your Atlas URI, API keys, etc.

# 4. Run any lab
python chapter-02/first_connection.py
python chapter-02/lab_02_bookstore_crud.py
```

---

## Project Structure

```
nosql-mongodb-labs/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── config/
│   ├── __init__.py
│   └── connection.py           # Shared MongoDB connection utility
├── chapter-01/                 # Why NoSQL?
│   ├── lab_01_classify_databases.py
│   └── lab_02_map_application.py
├── chapter-02/                 # Cloud Computing Primer
│   ├── first_connection.py
│   ├── lab_01_setup_environment.py
│   └── lab_02_bookstore_crud.py
├── chapter-03/                 # Data Model Fundamentals
│   ├── bson_exploration.py
│   ├── lab_01_embedded_schema.py
│   ├── lab_02_embed_vs_reference.py
│   └── schema_validation.py
├── chapter-04/                 # CRUD and Query Language
│   ├── lab_01_product_query_api.py
│   └── lab_02_upsert_bulk.py
├── chapter-05/                 # Aggregation Framework
│   ├── lab_01_sales_analytics.py
│   └── lab_02_lookup_joins.py
├── chapter-06/                 # Indexing Strategies
│   ├── lab_01_index_design.py
│   └── lab_02_index_strategies.py
├── chapter-07/                 # Architecture Deep Dive
│   ├── lab_01_production_schema.py
│   └── lab_02_working_set_analysis.py
├── chapter-08/                 # Replication & HA
│   ├── docker-compose-replicaset.yml
│   ├── lab_01_deploy_replicaset.sh
│   └── lab_02_failover_observer.py
├── chapter-09/                 # CAP Theorem in Practice
│   ├── lab_01_write_concern_latency.py
│   └── lab_02_simulate_partition.sh
├── chapter-10/                 # Transactions
│   ├── lab_01_bank_transfer.py
│   └── lab_02_inventory_reservation.py
├── chapter-11/                 # Sharding
│   ├── lab_01_shard_key_eval.py
│   └── lab_02_shard_key_hotspot.py
├── chapter-12/                 # Security & CIA Triad
│   ├── lab_01_rbac_setup.sh
│   ├── lab_02_tls_setup.sh
│   └── rbac_field_redaction.py
├── chapter-13/                 # Container/Cloud Deployment
│   ├── docker-compose-production.yml
│   ├── lab_01_deploy_prod.sh
│   ├── lab_02_k8s_statefulset.py
│   └── main.tf                # Terraform for Atlas
├── chapter-14/                 # Production Operations
│   ├── lab_01_monitoring_dashboard.py
│   └── lab_02_backup_restore.py
├── chapter-15/                 # Multi-Tenant SaaS Architecture
│   ├── lab_01_multitenant_api.py
│   └── lab_02_tenant_migration.py
├── chapter-16/                 # Polyglot Persistence
│   ├── lab_01_polyglot_modeling.py
│   └── lab_02_hybrid_query_service.py
├── chapter-17/                 # Vector Search & RAG
│   ├── lab_01_rag_pipeline.py
│   └── lab_02_hnsw_vs_ivf.py
├── chapter-18/                 # Comparative Capstone
│   ├── lab_01_comparative_capstone.py
│   └── lab_02_comparative_report.py
└── appendix-a/                 # Full LLM Chat App
    ├── chat_api.py             # FastAPI backend
    ├── streamlit_app.py        # Streamlit frontend
    ├── Dockerfile
    ├── docker-compose.yml
    └── ingest_sample_data.py
```

---

## Lab-to-Script Mapping

| Ch | Title | Lab Script | Requires |
|----|-------|-----------|----------|
| 1 | Why NoSQL? | `lab_01_classify_databases.py` | None (in-memory) |
| 1 | App Mapping | `lab_02_map_application.py` | MongoDB |
| 2 | Setup Env | `lab_01_setup_environment.py` | Docker (optional) |
| 2 | Bookstore CRUD | `lab_02_bookstore_crud.py` | MongoDB |
| 3 | Embedded Schema | `lab_01_embedded_schema.py` | MongoDB |
| 3 | Embed vs Ref | `lab_02_embed_vs_reference.py` | MongoDB |
| 3 | BSON Types | `bson_exploration.py` | MongoDB |
| 3 | Schema Validation | `schema_validation.py` | MongoDB |
| 4 | Product Query API | `lab_01_product_query_api.py` | MongoDB |
| 4 | Upsert & Bulk | `lab_02_upsert_bulk.py` | MongoDB |
| 5 | Sales Analytics | `lab_01_sales_analytics.py` | MongoDB |
| 5 | $lookup Joins | `lab_02_lookup_joins.py` | MongoDB |
| 6 | Index Design | `lab_01_index_design.py` | MongoDB |
| 6 | Index Strategies | `lab_02_index_strategies.py` | MongoDB |
| 7 | Production Schema | `lab_01_production_schema.py` | MongoDB |
| 7 | Working Set | `lab_02_working_set_analysis.py` | MongoDB |
| 8 | Deploy Replica Set | `lab_01_deploy_replicaset.sh` | Docker Compose |
| 8 | Failover Observer | `lab_02_failover_observer.py` | Replica Set (Ch 8) |
| 9 | Write Concern Latency | `lab_01_write_concern_latency.py` | Replica Set (Ch 8) |
| 9 | Simulate Partition | `lab_02_simulate_partition.sh` | Replica Set (Ch 8) |
| 10 | Bank Transfer | `lab_01_bank_transfer.py` | MongoDB 4.0+ |
| 10 | Inventory Reservation | `lab_02_inventory_reservation.py` | MongoDB 4.0+ (transactions) |
| 11 | Shard Key Eval | `lab_01_shard_key_eval.py` | None (analysis) |
| 11 | Shard Key Hotspot | `lab_02_shard_key_hotspot.py` | MongoDB (simulation, no real cluster needed) |
| 12 | RBAC Setup | `lab_01_rbac_setup.sh` | MongoDB + mongosh |
| 12 | TLS Setup | `lab_02_tls_setup.sh` | MongoDB + mongosh + OpenSSL |
| 12 | Field Redaction | `rbac_field_redaction.py` | MongoDB |
| 13 | Deploy Prod RS | `lab_01_deploy_prod.sh` | Docker Compose |
| 13 | K8s StatefulSet | `lab_02_k8s_statefulset.py` | kubectl + cluster (optional; generates manifests either way) |
| 13 | Terraform Atlas | `main.tf` | Terraform + Atlas account |
| 14 | Monitoring | `lab_01_monitoring_dashboard.py` | MongoDB |
| 14 | Backup & Restore | `lab_02_backup_restore.py` | MongoDB + Database Tools (mongodump/mongorestore) |
| 15 | Multi-Tenant API | `lab_01_multitenant_api.py` | MongoDB |
| 15 | Tenant Migration | `lab_02_tenant_migration.py` | MongoDB |
| 16 | Polyglot Modeling | `lab_01_polyglot_modeling.py` | None (comparison) |
| 16 | Hybrid Query Service | `lab_02_hybrid_query_service.py` | MongoDB (Neo4j optional; falls back to an in-memory graph) |
| 17 | RAG Pipeline | `lab_01_rag_pipeline.py` | MongoDB |
| 17 | HNSW vs IVF | `lab_02_hnsw_vs_ivf.py` | None (NumPy only, fully offline) |
| 18 | Comparative Capstone | `lab_01_comparative_capstone.py` | MongoDB |
| 18 | Comparative Report | `lab_02_comparative_report.py` | MongoDB (optional; falls back to labeled estimates if unreachable) |
| App | LLM Chat App | `appendix-a/` | FastAPI + Streamlit + Ollama/OpenAI |

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | All lab scripts |
| MongoDB | 7.0+ | Primary database |
| Docker | 20.10+ | Container-based labs (Ch 8, 13) |
| mongosh | 2.0+ | Shell scripts (Ch 8, 9, 12, 13) |
| pip | latest | Install Python packages |

**Optional (for specific chapters):**

| Tool | Chapter | Purpose |
|------|---------|---------|
| Ollama | 17, App | Local LLM inference |
| OpenAI API key | 17, App | GPT embeddings + chat |
| Terraform | 13 | Atlas infrastructure provisioning |
| kubectl + a cluster (minikube/kind/managed) | 13 | Kubernetes StatefulSet lab (manifests still generate without one) |
| MongoDB Database Tools | 14 | `mongodump`/`mongorestore` for the backup lab |
| OpenSSL | 12 | TLS certificate generation |
| Cassandra | 16, 18 | Wide-column comparison (labs run without it, using estimated figures) |
| Neo4j | 16, 18 | Graph database comparison (labs run without it, using estimated figures / an in-memory fallback graph) |

---

## Running the Labs

### Single script (standalone)

Every Python script can be run directly from the project root:

```bash
python chapter-04/lab_01_product_query_api.py
```

Each script imports the shared `config/connection.py` module, which reads
from `.env` for the MongoDB URI.

### Shell scripts

```bash
chmod +x chapter-08/lab_01_deploy_replicaset.sh
./chapter-08/lab_01_deploy_replicaset.sh
```

### Replica Set labs (Ch 8, 9)

These require a running 3-node replica set:

```bash
# Start the replica set
./chapter-08/lab_01_deploy_replicaset.sh

# In another terminal, observe failover
python chapter-08/lab_02_failover_observer.py

# Benchmark write concerns
python chapter-09/lab_01_write_concern_latency.py

# Simulate a network partition
chmod +x chapter-09/lab_02_simulate_partition.sh
./chapter-09/lab_02_simulate_partition.sh
```

### Labs with a graceful no-server fallback

A few labs are designed to still run (and still teach something) even
without every optional tool installed:

- `chapter-13/lab_02_k8s_statefulset.py` generates and validates the
  Kubernetes manifests even with no cluster reachable; it only attempts
  `kubectl apply` if a cluster is detected.
- `chapter-16/lab_02_hybrid_query_service.py` uses a real Neo4j connection
  if `NEO4J_URI` is set and the `neo4j` package is installed, otherwise
  falls back to an equivalent in-memory graph traversal.
- `chapter-17/lab_02_hnsw_vs_ivf.py` has no database dependency at all --
  it benchmarks vector-index strategies on a synthetic in-memory dataset.
- `chapter-18/lab_02_comparative_report.py` measures real MongoDB numbers
  if a database is reachable, otherwise falls back to labeled example
  figures so the report still generates -- and the report text always
  states which numbers were measured versus estimated.

### Appendix A - Full LLM Chat App

```bash
# Start MongoDB
docker run -d -p 27017:27017 --name chat-mongo mongo:7

# Option A: Run locally
pip install fastapi uvicorn streamlit openai requests
python appendix-a/ingest_sample_data.py  # populate RAG data
uvicorn appendix-a.chat_api:app --reload  # start backend
streamlit run appendix-a/streamlit_app.py --server.port 8501  # start frontend

# Option B: Docker Compose
# (requires Ollama running on host for LLM backend)
cd appendix-a && docker compose up --build
```

---

## Notes

- All Python scripts use `pymongo` and include error handling for connection failures.
- Shell scripts require `mongosh` (not legacy `mongo` shell).
- Chapters 8-9 labs require a replica set (use the Ch 8 docker-compose to set one up).
- Chapter 11 (Sharding) and Chapter 16's first lab (Polyglot Modeling) are analysis/design
  labs; Chapter 11's second lab and Chapter 16's second lab do use a standalone MongoDB
  to demonstrate the pattern in code, but neither requires a real sharded cluster or a
  real Neo4j instance to run.
- The Appendix A chat app works with mock embeddings by default. Set `OPENAI_API_KEY` or
  `VOYAGE_API_KEY` in `.env` for real embeddings.
- Every chapter from 1 through 18 has exactly two lab scripts (36 labs total), plus the
  Appendix A capstone. If you're looking for a chapter's "second lab" and only see one file
  in an older checkout, pull the latest version of this repo.
