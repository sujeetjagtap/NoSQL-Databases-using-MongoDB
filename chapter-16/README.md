# Chapter 16: Wide-Column and Graph Databases -- Cassandra and Neo4j

## What You'll Learn

- How the same real-world data (a fraud-detection scenario) gets modeled completely differently in MongoDB, Cassandra, and Neo4j -- and why each model follows from that database's own strengths
- Cassandra's column-family model: keyspaces, partition keys, and why the query pattern has to be known *before* you design the table (the opposite order from a document or relational model)
- Neo4j's property graph model: nodes, relationships, and why multi-hop traversal is native there in a way it isn't anywhere else
- Polyglot persistence as a real, working pattern: routing different query types to different databases within one application, based on each query's actual access pattern

## Prerequisites

MongoDB running locally or on Atlas. Neither Cassandra nor Neo4j is required to run either activity -- Activity 1 is a pure comparison script, and Activity 2 falls back to an in-memory graph if no real Neo4j connection is configured.

## Activity 1: Model Data in Three Databases [`lab_01_polyglot_modeling.py`]

### Topics You Need First

**The same fraud case, modeled three ways, reveals each database's real bias.** In MongoDB, a fraud case is one document with an embedded `linked_accounts` array and a `tags` array -- optimized for "fetch everything about this case in one read" and "filter by risk score and amount." In Cassandra, the same data becomes a table whose primary key is chosen specifically to make the most common query (recent cases for a given suspect) a fast partition scan, at the cost of needing a *different* table (denormalized, duplicated) for any other access pattern. In Neo4j, suspects and accounts become nodes connected by `LINKED_TO`/`SHARES_DEVICE` relationships -- because the question that actually matters ("who else is connected to this suspect, and how") is a graph traversal, not a filter.

**Cassandra's defining constraint: design the table around the query, not the entity.** Unlike MongoDB (query however you like against a flexible document) or a relational database (normalize first, query later with joins), Cassandra requires you to know your access pattern *before* choosing a partition key, because a query that doesn't align with the partition key either requires a full cluster scan or simply isn't supported without `ALLOW FILTERING` (a red flag, not a real solution).

**Neo4j's defining constraint: relationships have to be modeled as first-class things, not looked up.** Modeling "these two accounts share a device" as an edge with its own properties (which device, since when) is what makes "find everyone within 3 hops of this suspect" a native, efficient traversal -- the same query in MongoDB or Cassandra would require either `$graphLookup` (workable but not built for deep traversal) or an application-side breadth-first search over multiple round trips.

### The Task

The script prints, side by side, a schema and an equivalent representative query for the same fraud-case scenario in all three databases.

Before reading Neo4j's section: having already read MongoDB's and Cassandra's schemas, predict what the *relationship* modeling will look like in Neo4j, and predict what its "who is connected to this suspect" query will look like compared to MongoDB's `$graphLookup` equivalent. Then compare your prediction against the printed Cypher.

## Activity 2: Build a Hybrid Query Service [`lab_02_hybrid_query_service.py`]

### Topics You Need First

**Polyglot persistence means routing queries, not just "using two databases."** It's not enough to run MongoDB and Neo4j side by side -- a real hybrid system needs a routing layer that sends each incoming query to whichever database is actually suited to it: point lookups and attribute filters to MongoDB, multi-hop relationship traversal to Neo4j.

**The routing decision is mechanical once you know each database's strength.** "Get case FC-001" and "all cases with risk_score > 0.8" are both point/attribute queries &rarr; MongoDB. "Who shares a device with U-101, within 3 hops" is a graph traversal &rarr; Neo4j (or, absent a real Neo4j connection, an equivalent in-memory breadth-first search standing in for what Neo4j would do natively).

### The Task

The service seeds fraud cases into MongoDB and a small device-sharing graph (into real Neo4j if `NEO4J_URI` is configured, otherwise an in-memory graph), then answers three queries: a point lookup by case id, an attribute-range filter, and a multi-hop "who's connected to this suspect" traversal -- each routed to the appropriate backend.

Before reading the `HybridQueryService` class: for each of the three queries, decide for yourself which backend it should be routed to and why, referencing the routing logic explained above. Then check the printed "Routing Decision Table" at the end against your own reasoning.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_polyglot_modeling.py` | Activity 1 |
| `lab_02_hybrid_query_service.py` | Activity 2 (works with or without a real Neo4j instance) |

## Check Your Work

For Activity 1, you should be able to explain, for each of the three schemas, one query that would be *awkward or inefficient* in that database despite being natural in one of the other two (e.g., "find all cases above a risk threshold" is trivial in MongoDB, awkward in Cassandra without a dedicated table for it, and not what Neo4j is optimized for at all).

For Activity 2, the printed Routing Decision Table at the end should match your own pre-read predictions exactly -- if the multi-hop traversal query surprised you by not being routed to the graph backend, re-read the "polyglot persistence" explanation above, since that routing decision is the entire point of the activity.
