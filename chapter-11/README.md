# Chapter 11: Sharding and Horizontal Scalability

## What You'll Learn

- The four properties that make a good shard key: high cardinality, even distribution, query targeting, and non-monotonicity
- Why each of those properties matters *mechanically* -- not as rules to memorize, but as consequences of how MongoDB partitions data into chunks and routes queries
- What a "hotspot" actually looks like in practice: one shard doing disproportionately more work than the others
- Why a monotonically increasing shard key (like a timestamp or auto-incrementing id) is a specific, well-known anti-pattern

## Prerequisites

Activity 1 needs no database connection (it's a pure decision-framework script). Activity 2 needs MongoDB running locally or on Atlas.

## Activity 1: Evaluate Shard Key Choices [`lab_01_shard_key_eval.py`]

### Topics You Need First

**Cardinality** is how many distinct values a field can take. A shard key with low cardinality (like `category_id` with only 50 possible values) puts a hard ceiling on how many chunks MongoDB can meaningfully split your data into -- you can never have more useful shards than you have distinct key values.

**Distribution** is whether those distinct values are evenly popular. Even with high cardinality, if 90% of your documents share one value (a wildly popular product category, a single high-traffic tenant), that value's shard becomes a bottleneck no matter how many other shards exist.

**Query targeting** is whether your actual queries include the shard key in their filter. If most of your queries filter by `user_id` but your shard key is `order_id`, MongoDB can't route those queries to a single shard -- it has to broadcast to *every* shard and merge the results (a "scatter-gather" query), which is far slower than a targeted one.

**Monotonicity** is the property that breaks all of this at once. A shard key like `created_at` or an auto-incrementing id always increases -- which means every new document's key value falls into the *same* (currently-highest) chunk, so all writes land on one shard no matter how many shards you have. This is the single most common real-world sharding mistake.

### The Task

The script scores four candidate shard keys for an e-commerce system (`user_id` hashed, `order_id` hashed, `category_id`, and `created_at` as a range key) against all four properties, and prints a verdict for each.

Before reading the printed verdicts: for each candidate, predict whether it would be RECOMMENDED, GOOD-with-caveats, BAD, or AVOID -- and write down *which* of the four properties is the deciding factor in your reasoning. Then check both your verdict and your reasoning against the script's.

## Activity 2: Shard Key Hotspot Detection [`lab_02_shard_key_hotspot.py`]

### Topics You Need First

**A monotonic key concentrates writes even without a real sharded cluster to prove it.** You don't need to stand up an actual multi-shard cluster to demonstrate the hotspot problem -- you can simulate MongoDB's own chunk-assignment logic (hashing a key into a small number of buckets standing in for shards) against two candidate keys and directly compare how evenly documents land across those buckets.

**Hashing breaks monotonicity on purpose.** A hashed shard key takes a value (even a monotonically increasing one) and maps it to what looks like a effectively random bucket -- which is exactly why "hashed `_id`" or "hashed `created_at`" is a common real-world fix for a key that's otherwise good but monotonic.

### The Task

The script simulates document distribution across a small number of shard "buckets" using two candidate keys: a monotonically increasing timestamp-based key, and a hashed version of the same underlying value. It reports how many documents land in each bucket under each strategy.

Before running it, predict the shape of the two distributions: for the timestamp-based key, do you expect the documents to spread evenly across buckets, or concentrate heavily in one? For the hashed version of the same field, what changes? Then compare your prediction against the printed per-bucket counts.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_shard_key_eval.py` | Activity 1 |
| `lab_02_shard_key_hotspot.py` | Activity 2 |

## Check Your Work

For Activity 1, if you correctly flagged `created_at` (range key) as AVOID and identified monotonicity as the specific problem (not cardinality or distribution, which are actually fine for a date field), you've understood the concept precisely rather than just pattern-matching "dates are bad."

For Activity 2, a correct simulation should show the vast majority of documents landing in a single bucket (or the most-recent few buckets) under the raw timestamp key, and a roughly even spread across all buckets under the hashed version of the same key -- that contrast *is* the lesson, not an incidental detail.
