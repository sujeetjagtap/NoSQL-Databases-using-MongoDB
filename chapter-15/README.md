# Chapter 15: Designing and Architecting a MongoDB-Backed Product as a Service

## What You'll Learn

- The shared-collection-plus-tenant-id-field pattern for multi-tenant isolation: the simplest, cheapest isolation tier, and exactly where its safety depends entirely on application discipline
- Why every single query in a multi-tenant system has to filter by tenant, and what happens the moment one forgets to
- MongoDB-based rate limiting: implementing a sliding/fixed window counter directly in the database, without a separate service like Redis
- How to migrate a specific tenant to a stronger isolation tier (database-per-tenant) safely, idempotently, and with a rollback path -- without needing to redesign the whole system for every tenant at once

## Prerequisites

MongoDB running locally or on Atlas.

## Activity 1: Design a Multi-Tenant API [`lab_01_multitenant_api.py`]

### Topics You Need First

**Shared-collection isolation means every document from every tenant lives in the same collection, distinguished only by a `tenant_id` field.** It's the cheapest tier to run (one collection, one set of indexes, no per-tenant infrastructure) and the cheapest to get wrong: since MongoDB itself doesn't know about your tenants, *every* query, update, and delete must explicitly include `{"tenant_id": tenant_id}` in its filter, or it will silently operate across tenant boundaries.

**Look specifically at `update_task`'s filter.** It filters on `{"_id": task_id, "tenant_id": tenant_id}` together -- not just `{"_id": task_id}`. This is the one-line difference between "tenant A can only update tenant A's tasks" and "tenant A can update *any* tenant's task, as long as they guess or otherwise obtain its id." This single detail is the crux of the entire isolation model in this activity.

**Rate limiting as a database-native pattern.** Rather than a separate caching layer, `check_rate_limit` implements a request counter directly in MongoDB, scoped per tenant and per time window, using an upsert-and-check pattern -- appropriate when your rate-limit precision needs are modest and you'd rather not run a second piece of infrastructure just for this.

### The Task

Build (or read, then verify) a task-management API where tasks are created, listed, and updated, all scoped to a `tenant_id`, plus a rate limiter that rejects a tenant's requests once they exceed a configured number of calls within a time window.

Before reading `update_task`'s implementation: write down what would go wrong -- concretely, with an example -- if its filter only checked `{"_id": task_id}` without also checking `tenant_id`. Then confirm that scenario is exactly what the actual filter prevents.

## Activity 2: Data Migration Between Tenant Isolation Strategies [`lab_02_tenant_migration.py`]

### Topics You Need First

**Not every tenant needs the same isolation tier.** A small customer is usually fine sharing infrastructure via the `tenant_id` pattern from Activity 1. A large enterprise customer may have a compliance requirement (or just a risk tolerance) that calls for database-per-tenant isolation instead -- their own dedicated MongoDB database, physically separated from every other tenant's data. A real product supports moving a *specific* tenant between these tiers without re-architecting for everyone.

**Idempotency matters for migrations specifically because they might need to be re-run.** A migration script that gets interrupted partway through (a network blip, a restart) needs to be safely re-runnable from the start without creating duplicate data. This activity's migration uses an upsert keyed on a natural identifier (not the auto-generated `_id`, which would differ between runs) so re-running it converges to the same end state instead of piling up duplicates.

**A migration without a rollback path is a one-way door.** This activity's migration only *copies* data into the new isolation tier -- it never deletes anything from the shared collection until you're confident the new tier is stable. That's what makes the rollback (dropping the tenant's new dedicated database) safe: the original data was never at risk in the first place.

### The Task

The script migrates one specific tenant's data out of the shared `saas_app.tasks` collection (Activity 1's design) and into its own dedicated database. It supports a `--dry-run` mode (reports what *would* move, without writing anything), runs the real migration, then deliberately re-runs the exact same migration a second time to demonstrate idempotency, and supports a `--rollback` mode.

Before running the second (repeat) migration: predict whether the tenant's document count in the new database will double, stay the same, or something else. Then run it and confirm against the printed `target_count`.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_multitenant_api.py` | Activity 1 |
| `lab_02_tenant_migration.py` | Activity 2 (supports `--tenant`, `--dry-run`, and `--rollback` flags) |

## Check Your Work

For Activity 1, try (as an experiment, not part of the main script) calling `update_task` with the wrong `tenant_id` for an existing task's real `_id` -- it should return `False` / modify zero documents, proving the isolation filter is doing real work, not just documenting an intention.

For Activity 2, run the migration once, then run it again immediately (or use the script's own idempotency check) and confirm the tenant's document count in the new database is identical both times -- not doubled. Then run `--rollback` and confirm the tenant's dedicated database is gone while the original shared collection is completely untouched.
