# Chapter 4: Mastering Queries -- CRUD and the Query Language in Python

## What You'll Learn

- The full shape of a MongoDB query filter: comparison operators (`$gt`, `$gte`, `$lte`), logical operators (`$or`, `$and`), and array-field matching
- Projections (choosing *which fields* come back) and pagination (`skip`/`limit`) for query results
- `upsert` -- update-or-insert in a single atomic operation -- and why it's not just a convenience shortcut
- What "idempotent" actually means for a database write, and why some update operators (`$set`) are idempotent while others (`$inc`, `$mul`) are not -- a distinction that matters the moment you add retry logic to anything

## Prerequisites

MongoDB running locally or on Atlas (Chapter 2).

## Activity 1: Build a Product Query API [`lab_01_product_query_api.py`]

### Topics You Need First

**Comparison operators** live inside the filter's value: `{"price": {"$gte": 500, "$lte": 800}}` reads as "price is between 500 and 800 inclusive." This is different from SQL's `BETWEEN` syntactically but identical in meaning.

**Logical operators** combine multiple conditions: `{"$or": [{"category": "Laptops"}, {"category": "Monitors"}]}` matches either condition. Fields listed as siblings in the same filter document are implicitly AND-ed together -- so `{"$or": [...], "price": {"$gt": 600}}` means "(category is Laptops OR Monitors) AND price > 600."

**Array-field matching** works two ways: `{"tags": "mechanical"}` matches any document where `"mechanical"` appears *anywhere* in the `tags` array (no special operator needed). `$elemMatch` is for a stricter case: matching a single array element against *multiple* conditions at once, so that one element satisfies all of them together (rather than different elements each satisfying one condition).

**Projections and pagination.** The second argument to `.find()` is the projection -- `{"name": 1, "price": 1, "_id": 0}` returns only those fields. `search_products()` in this file builds `skip`/`limit` pagination on top of that: page 2 with page_size 3 means `skip((2-1)*3).limit(3)`.

### The Task

Seven realistic e-commerce products (laptops, monitors, keyboards -- with nested `specifications` and a `tags` array each) are seeded. The script then runs a sequence of queries you should try to write yourself first: a price range with comparison operators; laptops-or-monitors above a price threshold with a logical operator; every product tagged `"mechanical"`; every product with `stock > 10` AND `rating >= 4.5` using `$elemMatch`; a name+CPU-only projection restricted to laptops; and a paginated listing using the `search_products()` helper.

Before reading each query in the source, write your own MongoDB filter for the described result, then compare.

## Activity 2: Implement Upsert and Bulk Operations [`lab_02_upsert_bulk.py`]

### Topics You Need First

**Upsert** (`upsert=True` on an update) means: update the document if a match exists, otherwise insert a new one built from the filter + update. This collapses a common "check if it exists, then decide whether to insert or update" race condition into a single atomic server-side operation.

**Bulk writes** (`bulk_write([...])`) batch several `UpdateOne`/`InsertOne`/`DeleteOne` operations into one round trip to the server, instead of one network call per operation -- the difference between one request and N requests when importing/syncing many records at once.

**Idempotency, precisely.** An operation is idempotent if running it twice has the same effect as running it once. `$set: {"name": "X"}` is idempotent -- setting the same value again changes nothing. `$inc: {"stock": -10}` is **not** -- running it twice decrements stock by 20, not 10. This matters in practice whenever a client might retry a write after a timeout: if the first attempt actually succeeded server-side but the client never got the acknowledgment, a naive retry of a non-idempotent operation silently double-applies it.

### The Task

The script builds a bulk write mixing several `UpdateOne` operations against a product inventory -- some upserts (new SKUs that don't exist yet), some plain updates (`$set` on existing fields), and at least one `$inc`/`$mul`-style numeric adjustment. It runs the bulk write once, prints the resulting inventory state, then **runs the exact same bulk write a second time** and prints the state again.

Before looking at the second run's output: predict which fields will be unchanged the second time (the `$set` ones) and which will have moved again (the `$inc` one). Then verify against the actual printed stock value.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_product_query_api.py` | Activity 1 |
| `lab_02_upsert_bulk.py` | Activity 2 |

## Check Your Work

For Activity 1, each query section prints only the matching products -- cross-check the count and identity of what's returned against the seed data listed at the top of the file (all seven products are printed in the source with their price/tags/stock/rating, so you can verify each filter by eye).

For Activity 2, the giveaway of a correct understanding is the second bulk-write run: `$set`-based changes should be bit-for-bit identical to the first run's result, while any `$inc`/`$mul`-based field should have moved again. If you expected everything to stay the same on the second run, that's the exact misconception this activity is designed to correct.
