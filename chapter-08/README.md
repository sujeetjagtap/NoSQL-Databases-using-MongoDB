# Chapter 8: Replication and High Availability

## What You'll Learn

- What a replica set actually is: one primary accepting writes, one or more secondaries replicating from it, and (optionally) an arbiter that votes in elections but holds no data
- How a replica set election works: what triggers one, and how `priority` biases which member is likely to win
- How to observe replication with your own eyes: write to the primary, read the same data back from a secondary
- How to detect a failover programmatically from a PyMongo client, not just by watching `rs.status()` in a shell

## Prerequisites

Docker and Docker Compose installed. This chapter's two activities are meant to be run back-to-back in two terminals (Activity 1 deploys the replica set and stays up; Activity 2 connects to it while it's running).

## Activity 1: Deploy a Local Replica Set [`lab_01_deploy_replicaset.sh`]

### Topics You Need First

**A replica set is not three independent MongoDB servers -- it's one logical database made of three members.** Only one member (the primary) accepts writes at any given time. The others (secondaries) continuously replicate the primary's oplog (operation log) and can serve reads if you explicitly opt into that with `rs.secondaryOk()` or a read preference.

**Priority biases elections, it doesn't fix them.** `priority: 2` on one member makes it more likely to win an election and become primary compared to a `priority: 1` (default) member, but it's a bias, not a guarantee -- an election also depends on which members are healthy and reachable at the time.

**An arbiter votes but stores nothing.** `arbiterOnly: true` gives a member a vote in elections (useful for keeping an odd number of voters, which avoids split-vote ties) without needing it to store a full copy of the data -- useful when you want fault tolerance but don't want (or can't afford) a third full data-bearing node.

### The Task

Run this script to deploy a 3-node replica set locally with Docker Compose: two data-bearing members (one with higher priority) and one arbiter. It initiates the replica set, waits for the election to settle, checks `rs.status()`, then writes one document to the primary and reads it back from a secondary a couple of seconds later.

Before running Step 4 (the replication check): predict how long you'd expect the delay to be between "write succeeds on primary" and "the same document becomes visible on a secondary" -- is it milliseconds, or could it meaningfully lag under load? The script uses a fixed 2-second wait; consider whether that's generous or tight for real replication lag.

## Activity 2: Observe Failover and Election [`lab_02_failover_observer.py`]

### Topics You Need First

**Detecting a failover from application code is different from watching it in a shell.** A PyMongo client connected with the full replica set URI (`?replicaSet=rs0`, listing all members) automatically discovers which member is currently primary and routes writes there -- but *your application* still needs to notice when that primary changes, especially if you're logging or alerting on it. This activity polls `replSetGetStatus` in a loop to do exactly that.

**What actually happens during an election, from a client's perspective.** For a few seconds during an election, there is no primary at all -- writes will fail or block until a new primary is elected. This activity is designed to make you *watch* that gap happen, not just read about it.

### The Task

With Lab 8.1's replica set already running, run this script in one terminal. In a second terminal, force an election with `mongosh --eval 'rs.stepDown()'` against the current primary (the script prints this exact command for you at startup). Watch the first terminal detect and print the `*** FAILOVER: <old primary> -> <new primary> ***` line.

Before triggering the step-down: predict roughly how many seconds will pass between the `rs.stepDown()` command and the observer script detecting the new primary. Time it, and compare against your prediction.

## Files in This Directory

| File | Purpose |
|---|---|
| `docker-compose-replicaset.yml` | The 3-node replica set definition used by Activity 1 |
| `lab_01_deploy_replicaset.sh` | Activity 1 |
| `lab_02_failover_observer.py` | Activity 2 |

## Check Your Work

For Activity 1, success is seeing the document you inserted on the primary (`"Hello from replica set!"`) printed back when the script reads from the secondary in Step 4 -- if it's missing, either replication hasn't caught up yet (increase the sleep) or `rs.secondaryOk()` wasn't set (reads from secondaries are refused by default without it).

For Activity 2, a correct run shows exactly one `PRIMARY detected` line at startup, followed by exactly one `*** FAILOVER ***` line a few seconds after you run `rs.stepDown()` in the other terminal -- if you see repeated flapping between primaries, that usually means the replica set hasn't fully stabilized from Activity 1 yet; give it more time after `docker compose up` before stepping down.
