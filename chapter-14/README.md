# Chapter 14: Managing Database Services in Production

## What You'll Learn

- Which MongoDB server metrics (`serverStatus`) actually matter operationally: connection counts, op counters, and WiredTiger cache stats -- and how to turn raw numbers into threshold-based alerts
- The difference between logging metrics and *displaying* them, and why a production monitoring setup needs both
- Why a backup that has never been restored is not a verified backup -- and what "verified" actually means (matching document count *and* matching content, not just "the restore command exited successfully")
- The mechanics of `mongodump`/`mongorestore` as a backup/restore pair, and how to test disaster recovery on your own machine before you ever need it for real

## Prerequisites

MongoDB running locally or on Atlas. Activity 2 additionally requires the MongoDB Database Tools (`mongodump`, `mongorestore`) installed and on your PATH.

## Activity 1: Build a Monitoring Dashboard [`lab_01_monitoring_dashboard.py`]

### Topics You Need First

**`serverStatus` is MongoDB's built-in metrics endpoint.** It's a single admin command that returns a large document covering connections, operation counters, replication state, and WiredTiger internals. Production monitoring tools (Atlas's own charts, Prometheus exporters, etc.) are ultimately reading and graphing the same underlying data this activity reads directly.

**Metrics only become useful once you attach a threshold to them.** A raw number ("current connections: 340") tells you nothing on its own. The same number becomes actionable the moment you compare it against a known limit (your configured `maxIncomingConnections`) and decide at what percentage of that limit you want to be alerted *before* you actually run out.

**Logging and displaying serve different purposes.** Printing a metrics table to your terminal is for the human looking at it right now. Writing the same data to a log file (`logging.basicConfig(filename=...)`, used here) is for *later* -- for correlating a metrics spike against an incident that gets investigated after the fact, once the terminal session that would have shown it live is long gone.

### The Task

The script pulls live connection counts, operation counters, and WiredTiger cache metrics from your running MongoDB, formats them into a readable table, appends them to a log file, and checks them against a couple of built-in alert thresholds.

Before reading which thresholds the script checks: decide for yourself what you'd consider an alert-worthy connection count or cache-eviction rate for a small lab MongoDB instance (versus what you'd set for a real production cluster serving thousands of concurrent users) -- the "right" threshold is context-dependent, and recognizing that is as much the point as reading the metric itself.

## Activity 2: Automated Backup and Restore Verification [`lab_02_backup_restore.py`]

### Topics You Need First

**A backup you haven't restored is a hope, not a guarantee.** It's easy to schedule `mongodump` on a cron job and consider backups "handled." The actual guarantee only exists once you've proven that a `mongorestore` from that dump produces the *same data* you started with -- which is a different (and more work) claim than "the dump file exists and isn't zero bytes."

**Verification needs two checks, not one.** Document *count* matching is a weak check -- it would pass even if every restored document were silently corrupted, as long as the number of documents was right. This activity also computes a content checksum (independent of document insertion order or regenerated `_id` values, since `mongorestore` doesn't guarantee either stays the same) to catch corruption that a count alone would miss.

**RPO and RTO give backup verification a business meaning.** Recovery Point Objective (how much data you can afford to lose -- determined by your backup *frequency*) and Recovery Time Objective (how long you can afford to be down -- determined partly by how long a restore actually takes) are the two numbers a backup strategy exists to satisfy. Timing your own restore in this activity gives you a real number for the RTO side of that equation.

### The Task

The script seeds a collection with known data and records a checksum, backs it up with `mongodump`, deliberately drops the collection (simulating data loss), restores it with `mongorestore`, and then checks both the restored document count and content checksum against the originals.

Before running it: predict what would happen to the final verification if `mongorestore` succeeded but happened to drop or duplicate even a single document -- would the count check alone catch that? Would the checksum? Use that question to explain, in your own words, why the script checks both rather than stopping at the count.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_monitoring_dashboard.py` | Activity 1 (writes to a `logs/` subfolder created alongside this file) |
| `lab_02_backup_restore.py` | Activity 2 (writes timestamped backups to a `backups/` subfolder created alongside this file) |

## Check Your Work

For Activity 1, open the generated `logs/metrics.log` after running the script a few times and confirm each run appended a new timestamped line rather than overwriting the previous one -- that append behavior is what makes the log useful for later incident correlation.

For Activity 2, the script's final output should read `[OK] Restore verified: document count AND content checksum match.` -- if you deliberately want to see the failure path, try modifying one restored document's value between the dump and the drop, and confirm the checksum check (not just the count) is what catches the mismatch.
