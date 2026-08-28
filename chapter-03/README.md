# Chapter 3: MongoDB Data Model Fundamentals

## What You'll Learn

- BSON, and how it differs from plain JSON (it has real types -- dates, binary, `ObjectId` -- not just strings/numbers/booleans)
- The embedding vs. referencing decision: when to nest related data inside one document, and when to split it into a separate collection linked by an id
- JSON Schema validation: how to make MongoDB *enforce* a shape on a collection, even though it's schema-flexible by default
- How to query into nested/array fields with dot notation (`"schedule.days"`, `"enrolled_students.email"`)

## Prerequisites

MongoDB running locally or on Atlas (Chapter 2).

## Activity 1: Design an Embedded Document Schema [`lab_01_embedded_schema.py`]

### Topics You Need First

**Embedding, concretely.** In this activity, each `course` document contains an `enrolled_students` array *inside* it -- there's no separate `students` collection with a `course_id` foreign key. That's the embedding pattern: data that's always read together (a course and its roster) lives in one document, so reading a course's full roster is a single `find_one()`, not a join.

**JSON Schema validation.** MongoDB is schema-flexible by default (any document shape can go into any collection), but you can attach a `validator` to a collection at creation time that rejects documents not matching a JSON Schema. This activity creates the `courses` collection *with* a validator, then deliberately tries to insert an invalid document to prove the validator is actually enforced -- not just documented.

**Dot notation for nested/array fields.** `{"schedule.days": "Monday"}` matches any course document where the nested `schedule.days` array contains `"Monday"`. `{"enrolled_students.email": "..."}` does the same one level into an array of subdocuments. This is how you query *into* an embedded structure without pulling the whole document out first.

### The Task

Design and populate a `courses` collection where each course embeds its own schedule and its full list of enrolled students (name, email, grade). Enforce the shape with a JSON Schema validator at collection-creation time.

Once seeded, the script exercises the design with four real queries you should be able to predict before reading the output: courses meeting on Monday, all courses taught by a specific instructor (and their roster sizes), adding a new student to one specific course with `$push` (an update, not a re-insert of the whole document), and finding every course a single student (by email) is enrolled in across the whole collection. Finally, it attempts to insert a document missing required fields, to confirm the validator actually rejects it rather than silently accepting anything.

## Activity 2: Migrate from Referenced to Embedded Design [`lab_02_embed_vs_reference.py`]

### Topics You Need First

**Referencing, and why it's the other half of the decision.** A referenced design splits related data across two collections (e.g., `posts` and `comments`, where each comment stores a `post_id` pointing back to its post) instead of nesting one inside the other. This is closer to how a relational schema would model the same data -- and it requires an application-level "join" (a second query, or a `$lookup` -- covered in Chapter 5) to reassemble a post with its comments.

**Why you'd migrate *to* embedded, not just start there.** Referencing is the right starting point when the "many" side is unbounded or needs to be queried independently (comments on a busy post can number in the thousands, and you might want to paginate them separately from the post). Embedding is right when the "many" side is small, bounded, and always read together with its parent. This activity builds both versions of the *same* data so you can compare them directly rather than trusting a description of the trade-off.

### The Task

Part A builds the referenced (normalized) design: a `posts` collection and a separate `comments` collection, each comment linking back via `post_id`. Part B rebuilds the same logical data as an embedded design: each post document contains its comments directly.

Before running past Part A's output: write down what query (or queries) you'd need to fetch "a post and all its comments" in the referenced design, versus the embedded design. Confirm your two-query vs. one-query answer against what the script actually does in each part.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_embedded_schema.py` | Activity 1 |
| `lab_02_embed_vs_reference.py` | Activity 2 |
| `bson_exploration.py` | Standalone demo of BSON types (ObjectId, Date, Binary, etc.) vs. plain JSON -- read this first if BSON is new to you |
| `schema_validation.py` | Standalone, more focused JSON Schema validation demo -- useful if you want to see validation in isolation before Activity 1 combines it with embedding |

## Check Your Work

For Activity 1: the validator-rejection test should print `[OK] Validation caught error: ...` -- if you instead see `[ERROR] Validation should have failed!`, the validator isn't wired up correctly, which is itself a useful failure to understand before moving on.

For Activity 2: compare the *shape* of what comes back from a "get post with comments" read in each part. In the referenced version you should see two separate result sets that your own code would have to merge; in the embedded version, one document already contains everything. That difference -- not which one is "better" -- is the actual lesson.
