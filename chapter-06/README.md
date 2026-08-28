# Chapter 6: Indexing Strategies and Performance Tuning

## What You'll Learn

- How to read `explain()` output: specifically the difference between a `COLLSCAN` (full collection scan) and an `IXSCAN` (index scan), and why that difference matters at scale
- Compound indexes: how field order inside an index changes which queries it can serve efficiently
- The ESR rule (Equality, Sort, Range) for ordering fields in a compound index
- The real cost side of indexing: every index speeds up some reads but slows down every write, because the index itself has to be updated on every insert
- Covered queries: when an index alone contains every field a query needs, so MongoDB never has to fetch the full document at all

## Prerequisites

MongoDB running locally or on Atlas (Chapter 2). This chapter inserts 50,000-60,000 synthetic documents, so allow a few seconds for seeding.

## Activity 1: Index Design for a Query Workload [`lab_01_index_design.py`]

### Topics You Need First

**`explain()` output, the two numbers that matter most.** `totalDocsExamined` is how many documents MongoDB had to look at; `totalKeysExamined` is how many index entries it had to look at (0 if no index was used). A `COLLSCAN` with `totalDocsExamined` equal to the full collection size means MongoDB read every single document to answer your query -- the thing indexes exist to prevent.

**Compound indexes and field order.** An index on `{"level": 1, "service": 1}` can efficiently serve queries that filter on `level` alone, or on `level` AND `service` together -- but it can *not* efficiently serve a query that filters on `service` alone, because a compound index is only useful as a left-to-right prefix (the same reason a phone book sorted by last-then-first name doesn't help you find everyone with a given first name).

### The Task

50,000 synthetic server log entries (level, service, status code, response time) are generated and inserted with **no indexes**. The script runs three realistic queries (errors from a specific service; all 404 responses; slow requests from a specific service) and shows you their `explain()` output -- all three should show a `COLLSCAN`.

Before the script creates any index: for each of the three queries, decide what compound index (which fields, in what order) would make it efficient. Then compare your answer against the three indexes the script actually creates, and check the *second* set of `explain()` output to confirm each query now uses an `IXSCAN` instead of a `COLLSCAN`.

## Activity 2: Compare Index Strategies [`lab_02_index_strategies.py`]

### Topics You Need First

**Indexes aren't free.** Every index has to be updated on every write that touches an indexed field. More indexes means faster reads for the queries they serve, but slower writes across the board, because each insert now has to update every index, not just append to the collection. This activity measures that trade-off directly rather than asserting it.

**Covered queries.** If a query's filter *and* its projection only reference fields that exist in an index, MongoDB can answer the query directly from the index without ever touching the underlying document. This is meaningfully faster than a normal indexed query (which still fetches the full document after finding it via the index) -- but only when the projection is narrow enough to be fully "covered."

**The ESR rule.** For a compound index supporting a query with an equality filter, a sort, and a range filter, the recommended field order is Equality fields first, then Sort fields, then Range fields. Putting a range field before a sort field (or before an equality field) breaks the index's ability to serve the sort efficiently, even though the index still "matches" the query in a loose sense.

### The Task

The script benchmarks 10,000 inserts into a collection with zero indexes vs. the same insert into a collection with five indexes already built, and prints the write-throughput overhead as a percentage. It then benchmarks 1,000 reads of the same query as a normal (non-covered) query vs. a covered one, and prints the speedup.

Before running it: predict whether the write overhead will be closer to 10% or closer to 100%, and predict whether the covered-query speedup will be closer to 1.5x or closer to 10x. Then check your intuition against the actual printed numbers -- the goal is calibrating your sense of *how much* these trade-offs cost, not just knowing the direction.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_index_design.py` | Activity 1 |
| `lab_02_index_strategies.py` | Activity 2 |

## Check Your Work

For Activity 1, the "Index Summary" printed at the end lists every index by name and key pattern -- confirm that the three indexes you predicted for the three queries appear there, and that the "with indexes" `explain()` output for each query shows `IXSCAN`, not `COLLSCAN`.

For Activity 2, if your write-overhead prediction and the covered-query speedup prediction were both roughly right, you've internalized the actual cost model of indexing rather than just the slogan "indexes make reads faster." If either was off by an order of magnitude, re-read the ESR rule explanation above and re-run the script with your own added indexes to build better intuition.
