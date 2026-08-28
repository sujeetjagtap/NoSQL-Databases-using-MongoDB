# Chapter 1: Why NoSQL? Foundations and the Database Landscape

## What You'll Learn

- The four core NoSQL families -- key-value, document, wide-column, and graph -- and what structural assumption each one makes about your data
- Why those assumptions make each family good at some access patterns and bad at others (there is no "best" database, only the right one for a workload)
- How NoSQL's trade-offs differ from a relational database's: schema flexibility vs. enforced structure, horizontal scale-out vs. vertical scale-up
- How to read a short "read/write pattern" description and map it to a database family, which is the core skill real architects use when picking a data store for a new service

## Prerequisites

None. This chapter's activities run entirely against a local or Atlas MongoDB instance and need no other service. See the repo-root README for MongoDB setup if you haven't connected yet.

## Activity 1: Classify Database Products [`lab_01_classify_databases.py`]

### Topics You Need First

**The four NoSQL families, concretely:**
- **Key-Value** -- a giant hash map: one key maps to one opaque value. No structure inside the value is visible to the database. Fastest possible reads/writes, but you can only ever ask "what's the value for this key?"
- **Document** -- like key-value, but the value is a structured document (JSON/BSON) the database *can* see inside, index, and query by field. MongoDB is the canonical example.
- **Wide-Column (Column-Family)** -- rows are grouped into "column families," and the database is built around fast writes and range scans over a partition key. Apache Cassandra is the canonical example.
- **Graph** -- data is stored as nodes and edges, optimized for traversing relationships (friend-of-a-friend, shortest path) rather than for scanning or filtering by attribute. Neo4j is the canonical example.

**Why this classification matters:** every one of these choices is a bet on your *access pattern*, not your data size. A key-value store isn't "worse" than a document store -- it's optimized for a narrower, faster job (pure lookup by key), and it gives up the ability to query by anything else in exchange.

### The Task

The script inserts ten real, named database products (MongoDB, Redis, Cassandra, Neo4j, Elasticsearch, and others) each tagged with its family, data model, vendor, and typical use case. It prints them grouped by family, then hands you three "mystery" products (DynamoDB, InfluxDB, OrientDB) with only a one-line hint each, and asks you to classify each one into a family *before* the script reveals its own answer.

Your job, before reading the printed answer: for each mystery product, decide which family (or families -- some products are multi-model) it belongs to, and be able to say *why* based on the hint alone.

## Activity 2: Map a Real-World Application to NoSQL Families [`lab_02_map_application.py`]

### Topics You Need First

**Read/write pattern as a design input.** The single most useful question when picking a database for one piece of an application is: *how is this specific data actually going to be read and written?* Not "how big is it," not "is it structured" -- but things like:
- Is it read-heavy or write-heavy?
- Does it need range scans over time (e.g., "all events between two dates")?
- Does it need multi-hop relationship traversal, or just point lookups?
- Does it need strong consistency (must never show a stale value) or is eventual consistency fine?

**Polyglot persistence** -- the practice of using more than one database family within a single application, because different parts of that application have genuinely different access patterns. This is the pattern this activity is building intuition for, and it's revisited concretely in Chapter 16.

### The Task

The script walks through two real application types -- a ride-sharing app and a social media analytics platform -- and, for each, breaks it into four data domains (e.g., for ride-sharing: user profiles, ride history, real-time GPS tracking, payment transactions). For each domain it prints a description and a read/write pattern.

Before looking at the script's `recommended_family` / `recommended_db` / `rationale` fields for each domain: read the description and read/write pattern, and decide for yourself which NoSQL family fits and why. Then compare your reasoning against the script's rationale -- the goal isn't to get the "correct" database name, it's to check whether your reasoning about *why* matches.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_classify_databases.py` | Activity 1 |
| `lab_02_map_application.py` | Activity 2 |

Both scripts use the shared `config/connection.py` helper (one directory up) to connect to MongoDB, print a results table, and reset their own collection on every run so you can re-run them freely.

## Check Your Work

Run each script only *after* you've written down your own answer for the mystery products (Activity 1) and your own family/database pick for each domain (Activity 2). The scripts are self-checking: they print the "expected" classification or the built-in rationale at the end, so you can compare directly rather than needing a separate answer key.

If your reasoning differs from the script's rationale, that's not necessarily wrong -- NoSQL family choice is a trade-off, not a single correct answer. Focus on whether you can defend your choice using a real property of the access pattern (throughput, consistency, traversal depth), not just a guess.
