# Chapter 2: Cloud Computing Primer and Environment Setup

## What You'll Learn

- The IaaS / PaaS / SaaS / DBaaS spectrum, and specifically what "managed database service" means operationally (who patches it, who scales it, who's paged when it's down)
- How to stand up MongoDB two ways: locally via Docker (fast, disposable, no account needed) and on MongoDB Atlas (managed, free tier, closer to how you'd run it in production)
- How to verify a Python environment end-to-end: interpreter, PyMongo driver, and an actual live connection -- the three things that silently break most people's first lab
- Basic CRUD (Create, Read, Update, Delete) with PyMongo against a realistic, nested document

## Prerequisites

- Python 3.10+
- Docker (recommended, for the local MongoDB option) -- see repo-root README Quick Start
- A MongoDB Atlas account (optional, only needed if you want to test the cloud path)

## Activity 1: Environment Setup Verification [`lab_01_setup_environment.py`]

### Topics You Need First

**Why "it can't connect" is almost never a MongoDB problem.** In practice, most first-lab failures are one of: the Python interpreter version, the `pymongo` package not installed, MongoDB not actually running (vs. installed), or a firewall/network issue between your machine and Atlas. This activity exists to check all four *before* you write a single line of application code, so that when Activity 2 fails, you already know your environment isn't the cause.

**Local vs. Atlas, and why both matter.** Local Docker MongoDB is disposable and fast to reset -- ideal for the labs in Chapters 1-12. Atlas is the managed cloud path you'll actually use from Chapter 13 onward (deployment, production ops, and the Terraform lab in Chapter 13 specifically provision Atlas). Verifying both now means neither is a surprise later.

### The Task

Run the script with no arguments. It checks, in order: your Python version, whether `pymongo` is importable, whether a local MongoDB is reachable on `localhost:27017`, whether an Atlas URI (if you've set `MONGO_URI_ATLAS` in `.env`) is reachable, whether Docker is installed and whether a `mongo:7` container is currently running, and finally which optional packages (FastAPI, Streamlit, Neo4j driver, etc.) used by later chapters are already installed.

There's no "correct answer" to produce here -- the task is to get from a red/failing checklist to a green one. If MongoDB Local shows NOT RUNNING, that's your cue to run the Docker command the script prints for you, not to move on and hope later labs work anyway.

## Activity 2: Bookstore CRUD Operations [`lab_02_bookstore_crud.py`]

### Topics You Need First

**CRUD in PyMongo, concretely:**
- **Create**: `collection.insert_many(list_of_dicts)` -- MongoDB documents are just Python dicts (which become BSON on the wire); there's no separate schema-definition step before you can insert.
- **Read**: `collection.find(filter_dict, projection_dict)` -- the first argument selects *which* documents match, the second selects *which fields* come back. `{"year": {"$gt": 2020}}` reads as "year greater than 2020" -- `$gt` is a query operator, not a typo.
- **Update**: `collection.update_many(filter, {"$mul": {"price": 1.10}})` -- updates use operators too; `$mul` multiplies a field in place rather than requiring you to read-modify-write in application code.
- **Delete**: `collection.delete_one(filter)` removes the first matching document; `delete_many` removes all matches.

**Why the book documents are nested.** Each book document includes a `publisher` field that is itself an object (`{"name": ..., "location": ...}`), not a separate table with a foreign key. This is the embedding pattern from Chapter 3 previewed early: data that's always read together lives in one document.

### The Task

The script seeds five real technical books (each with nested publisher info and a tags array), then performs, in sequence: a read filtered by year, a read filtered by genre, a read filtered by a numeric price range, a read filtered by an array field (`tags`), a bulk 10% price increase, and finally a deletion of one specific book by title.

Before running it, for each of the four read queries, write down what MongoDB filter document you'd use (e.g., "books published after 2020" &rarr; `{"year": {"$gt": 2020}}`) -- then check your filter against the one in the script's source.

## Files in This Directory

| File | Purpose |
|---|---|
| `first_connection.py` | A minimal standalone connectivity check -- not a graded lab, but useful to run first if you just want to confirm MongoDB is reachable without the full checklist |
| `lab_01_setup_environment.py` | Activity 1 |
| `lab_02_bookstore_crud.py` | Activity 2 |

## Check Your Work

For Activity 1, success looks like: "Core checks passed: 3/3" (or better) and the closing message "You are ready to start the labs!" If you're stuck below that, the printed remediation hints (e.g., the exact `docker run` command) are meant to be followed literally, not just read.

For Activity 2, run the script and compare its printed output at each stage against what you predicted: the "after 2020" list should contain exactly the books with `year > 2020`, the price-increase step should show every price scaled by exactly 1.10, and the final collection listing should be missing "Clean Code" and nothing else.
