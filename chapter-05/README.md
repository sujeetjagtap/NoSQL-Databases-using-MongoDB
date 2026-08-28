# Chapter 5: Aggregation Framework and Advanced Querying

## What You'll Learn

- The aggregation pipeline model: a sequence of stages, each transforming the documents that flow out of the previous stage
- `$group` for computing sums/counts/averages per key (MongoDB's equivalent of SQL's `GROUP BY`)
- `$lookup` for joining across collections, including the "left join" pattern for finding things with *no* match on the other side
- `$unwind`, `$project`, and pipeline sub-expressions (`let` / `$$pid`) for reshaping documents mid-pipeline

## Prerequisites

MongoDB running locally or on Atlas (Chapter 2).

## Activity 1: Build a Sales Analytics Pipeline [`lab_01_sales_analytics.py`]

### Topics You Need First

**The pipeline mental model.** An aggregation is a list of stages: `[{"$match": ...}, {"$group": ...}, {"$sort": ...}]`. Each stage takes the documents that came out of the stage before it and produces a new set of documents for the next stage -- similar to piping commands together in a shell, except each stage is a declarative transformation rather than an imperative one.

**`$group`.** The `_id` field of a `$group` stage is the key you're grouping *by* -- it can be a single field (`"$category"`), a compound key (an object of several fields), or even `null` (grouping everything into one bucket for a grand total). Every other field in the stage is an accumulator: `{"$sum": 1}` counts documents, `{"$sum": "$amount"}` sums a field, `{"$avg": "$price"}` averages it.

**Multi-stage pipelines build up an analysis incrementally.** A realistic pipeline is rarely one stage -- you typically `$match` to filter down to relevant documents first (so later stages process less data), then `$group` to aggregate, then `$sort` to order the result, then maybe `$limit` to a top-N.

### The Task

Working from a seeded `orders` collection, build (or predict, then verify) a multi-stage pipeline that answers: total revenue by category, the top N customers by total spend, and orders bucketed into categories by order size (e.g., small/medium/large) using conditional logic inside the pipeline.

Before running the script, sketch the stage sequence you'd use for "total revenue per category, highest first" on paper -- it should be exactly three stages (`$group`, then `$sort`, and optionally a preceding `$match`). Then compare against the actual pipeline in the source.

## Activity 2: Join Data with `$lookup` [`lab_02_lookup_joins.py`]

### Topics You Need First

**`$lookup` is MongoDB's join.** `{"$lookup": {"from": "customers_join", "localField": "customer_id", "foreignField": "customer_id", "as": "customer"}}` attaches, to each order document, an array field called `customer` containing every document from `customers_join` whose `customer_id` matches. Since it's always an array (even when exactly one match exists), it's typically followed by `$unwind` to flatten that single-element array back into a plain field.

**The "left join to find non-matches" pattern.** To find products that were *never* ordered, you `$lookup` from `products` into `orders` using a pipeline-style lookup (with `let`/`$$pid` to reference the outer document's field inside the sub-pipeline), then filter for documents where the resulting joined array is empty. This is the same shape as SQL's `LEFT JOIN ... WHERE right.id IS NULL`, expressed as an aggregation instead.

**`$project` reshapes the output.** After a `$lookup` + `$unwind`, you typically don't want the entire nested customer object in the output -- `$project` lets you pick specific fields, including reaching into the newly-joined subdocument (`"$customer.name"`) to pull just what you need.

### The Task

Three collections are seeded: orders (each referencing a customer and a list of products by id, including one order with zero products), customers, and products. The script builds three pipelines: (1) every order enriched with its customer's name/tier/city, (2) every product that was never ordered by anyone (the left-join pattern), and a third variation of your choosing based on the same data.

Before reading pipeline 2 in the source: write down, in your own words, what has to be true about the `$lookup`'d array for a product to count as "never ordered." Then check that your answer matches the actual filter condition used.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_sales_analytics.py` | Activity 1 |
| `lab_02_lookup_joins.py` | Activity 2 |

## Check Your Work

For Activity 1, your hand-written pipeline for "revenue by category, highest first" should produce output rows in strictly descending revenue order -- if it isn't sorted, you likely put `$sort` before `$group` (which sorts the raw orders, not the grouped totals) instead of after.

For Activity 2, the "never ordered" list should contain products whose `product_id` does not appear in *any* order's `product_ids` array in the seed data at the top of the file -- manually cross-check one or two against the seed data to confirm the left-join logic actually excludes everything that *was* ordered.
