# Chapter 7: MongoDB Architecture Deep Dive

## What You'll Learn

- How to reason about embed vs. reference with an actual number attached, using `$bsonSize` to measure document size rather than guessing
- What the "16MB document size limit" means in practice, and how comment-heavy embedded documents can approach it
- The "working set" concept: the subset of your data that's actively being read/written, and why it -- not your total data size -- is what determines whether MongoDB feels fast
- How to read WiredTiger cache metrics (`serverStatus`) to tell whether your working set fits in available memory

## Prerequisites

MongoDB running locally or on Atlas (Chapter 2). Activity 2 inserts 100,000 documents (~2KB each, roughly 200MB total), so make sure your environment has room for that.

## Activity 1: Analyze a Production Schema [`lab_01_production_schema.py`]

### Topics You Need First

**`$bsonSize` turns "should I embed or reference?" into a measurable question.** Chapter 3 introduced the embed-vs-reference decision qualitatively. This activity makes it quantitative: `{"$bsonSize": "$$ROOT"}` inside an aggregation pipeline returns the actual byte size of a document, so you can directly measure how large a blog post document gets as its embedded comments array grows, rather than reasoning about it in the abstract.

**The 16MB document size limit is a hard ceiling, not a soft guideline.** MongoDB rejects any single document exceeding 16MB. A blog post that embeds an unbounded comments array is a design that *will* eventually break in production, even if it works fine with the 3-8 comments per post seeded in this activity -- the point of measuring size now is to catch that kind of unbounded-embedding risk before it becomes a production incident.

### The Task

Seeded blog posts each embed a small `comments` array. The script measures each post's BSON size with `$bsonSize`, and you're asked to reason about what happens to that size as the comment count grows -- specifically, at what comment-count-per-post would a single blog post's embedded design start to approach a meaningful fraction of the 16MB limit, if comments kept accumulating over the life of a popular post (think: a post with tens of thousands of comments).

Before reading the script's own commentary: decide for yourself whether "embed all comments in the post document" is a safe design for *this specific* workload (a blog, where popular posts can accumulate comments indefinitely), or whether it's the kind of design that only looks safe because the seed data is small.

## Activity 2: Working Set Analysis [`lab_02_working_set_analysis.py`]

### Topics You Need First

**Working set vs. total data size.** Your total data size is everything on disk. Your working set is the subset that's actually being actively read or written *right now*. A 500GB collection where only the most recent 5GB is ever queried has a working set of ~5GB -- and if that 5GB fits in RAM (via the WiredTiger cache), performance stays fast regardless of the other 495GB sitting untouched on disk.

**Reading `serverStatus`'s WiredTiger cache metrics.** `cache.bytes currently in the cache` vs. `cache.maximum bytes configured` tells you how full the cache is. `eviction pages evicted by application threads` rising alongside `pages read into cache` is the signature of a working set that no longer fits: MongoDB is having to constantly evict old pages to make room for newly-requested ones, instead of keeping hot data resident.

### The Task

100,000 ~2KB documents (roughly 200MB total) are inserted, after which the script prints the WiredTiger cache metrics and simulates three range queries hitting different parts of the collection (the very beginning, the middle, and the very end), timing each one.

Before running the query timings: predict whether all three ranges will take roughly the same amount of time, or whether some will be noticeably slower -- and if you predict a difference, say which range you expect to be slowest and why (hint: think about what's most likely to still be in cache versus what's had time to be evicted).

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_production_schema.py` | Activity 1 |
| `lab_02_working_set_analysis.py` | Activity 2 |

## Check Your Work

For Activity 1, if you concluded that unbounded embedded arrays are risky for high-growth fields (comments, event logs, activity feeds) but fine for genuinely bounded ones (a user's list of 3-5 shipping addresses), you've got the right mental model -- the size limit isn't really about today's document size, it's about whether the field's growth is bounded by anything in your application's logic.

For Activity 2, the printed "Approx cache hit ratio" at the end is your direct evidence: a ratio close to 100% means the whole 200MB working set comfortably fit in the WiredTiger cache on your machine, while a lower ratio (more likely on a memory-constrained container or VM) is exactly the "working set exceeds cache" scenario the `[TIP]` line at the end is warning about.
