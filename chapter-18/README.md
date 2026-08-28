# Chapter 18: Comparative Capstone Lab

## What You'll Learn

- How to design and run a fair, reproducible benchmark across query types with genuinely different access patterns, on a single realistic dataset (synthetic financial transactions with a known fraud rate)
- How to turn 18 chapters of individual concepts into one architecture decision: which database(s) you'd actually choose for a specific real workload, and why
- How to write up a technical comparison the way a real team would decide between database options -- with a clear line between measured numbers and estimated/architectural claims
- Why "no single database wins every query pattern" is usually the correct answer, and how to reason about a polyglot architecture instead of forcing one winner

## Prerequisites

MongoDB running locally or on Atlas. Neither Cassandra nor Neo4j is required -- this capstone benchmarks MongoDB directly and reasons about the other two architecturally, exactly as a real team would before provisioning infrastructure they don't have yet.

## Activity 1: Comparative Capstone Lab [`lab_01_comparative_capstone.py`]

### Topics You Need First

**This activity is a synthesis, not a new concept.** By this point you've covered CRUD (Ch 4), aggregation (Ch 5), indexing (Ch 6), transactions (Ch 10), and the wide-column/graph comparison (Ch 16). This activity's job is to make you *apply* all of that to one coherent scenario, rather than introduce anything new.

**Why fraud detection specifically.** It's a workload that genuinely stresses different access patterns at once: point lookups (a specific transaction), attribute filtering (all high-risk transactions above a threshold), analytics (spending patterns by category), and -- if you extend it -- relationship traversal (accounts sharing a device, a job better suited to Neo4j, as Chapter 16 covered). A fair benchmark needs a workload that isn't secretly biased toward the database being tested.

**Benchmark methodology matters as much as the numbers.** A benchmark that only measures one query type "proves" whichever database is best at that one thing. This activity deliberately runs four different query types (see below) precisely so no single database's strength dominates the conclusion.

### The Task

10,000 synthetic transactions (with a known ~2% fraud rate, realistic fields like merchant, category, location, device id) are generated and inserted into MongoDB with appropriate indexes. The script then runs and times four benchmark queries: transaction history for a specific user, high-risk transaction filtering, category-based analytics (an aggregation), and a write-throughput test.

Before running the benchmark: for each of the four query types, predict whether you'd expect MongoDB to perform well or poorly *relative to Cassandra and Neo4j* (not in absolute terms) -- referencing what you learned about each database's strengths in Chapter 16. Then run the benchmark and read the printed latencies, and separately reason through whether your Cassandra/Neo4j predictions (which this script can't measure directly) still hold up.

## Activity 2: Write a Comparative Analysis Report [`lab_02_comparative_report.py`]

### Topics You Need First

**A real technical comparison document has a specific shape.** Executive Summary, Architecture, Query Performance Comparison, Data Modeling Analysis, Scalability Assessment, and a Final Recommendation is not an arbitrary template -- it's the structure a team would actually need to make and defend a database choice to stakeholders who weren't in the room for the benchmarking.

**Measured vs. estimated has to stay visibly separate.** This report pulls real, measured numbers from Activity 1's live MongoDB benchmark, but Cassandra and Neo4j numbers are architectural estimates (since this repo doesn't require you to stand up either) -- and the report explicitly labels which is which throughout, rather than blending them into a single table that implies everything was measured the same way. This is the single most important habit in writing any comparison you didn't fully benchmark yourself.

### The Task

Running this script reuses Activity 1's own benchmark functions to pull live MongoDB numbers (falling back to labeled example figures if no MongoDB is reachable), combines them with architectural estimates for Cassandra and Neo4j, and writes a complete Markdown report to a `reports/` subfolder.

Before reading the generated report's Final Recommendation section: write your own one-paragraph recommendation for this fraud-detection workload, based on everything you've read in this chapter and Chapter 16. Then compare your reasoning against the report's -- not to see if you got the "right" database name, but to check whether your argument holds up against the same evidence.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_comparative_capstone.py` | Activity 1 |
| `lab_02_comparative_report.py` | Activity 2 (writes to a `reports/` subfolder created alongside this file) |

## Check Your Work

For Activity 1, your pre-benchmark predictions about relative strengths should generally hold: MongoDB should perform comparatively well on the indexed point lookup and the aggregation, and the write-throughput test is where you'd expect Cassandra (not benchmarked here, but reasoned about) to have a structural edge based on Chapter 16.

For Activity 2, open the generated report and confirm it explicitly states, in its own text, which numbers were measured and which were estimated -- if that distinction isn't visibly present, the report has lost the one property that makes it trustworthy to a reader who wasn't in the room when it was generated.
