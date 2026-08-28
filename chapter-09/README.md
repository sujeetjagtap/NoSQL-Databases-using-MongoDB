# Chapter 9: The CAP Theorem in Practice

## What You'll Learn

- What write concern (`w:1`, `w:majority`, `w:all`) actually controls: how many replica set members must acknowledge a write before MongoDB tells your application it succeeded
- The direct, measurable latency cost of stronger consistency guarantees -- not just the theoretical trade-off, but real millisecond numbers from your own machine
- What `j:true` (journal acknowledgment) adds on top of write concern, and why it's a separate dial from replication
- How a network partition actually behaves from the client's point of view: what keeps working, what stops, and why

## Prerequisites

A running replica set (deploy it with Chapter 8's `lab_01_deploy_replicaset.sh` first, and leave it running). Activity 2 also requires Docker (to simulate disconnecting a container from its network).

## Activity 1: Measure Write Concern Latency [`lab_01_write_concern_latency.py`]

### Topics You Need First

**Write concern is a per-write choice, not a global server setting.** `w:1` means "the primary accepting the write is enough -- don't wait for anyone else." `w:majority` means "wait until a majority of voting members (primary included) have applied the write." `w:all` waits for every member. You choose this per-operation in your own application code, trading latency for durability guarantees exactly where you need to.

**Why `w:majority` is slower, mechanically, not just "by convention."** With `w:1`, the primary can acknowledge as soon as *it* has the write. With `w:majority`, the primary has to wait for at least one secondary to also replicate and apply that write before acknowledging -- which means at least one extra network round-trip to a secondary, every single write.

**`j:true` is a different axis entirely.** It controls whether MongoDB waits for the write to be flushed to the on-disk journal (surviving a hard crash) before acknowledging, independent of how many replica set members have seen it. `w:majority, j:false` and `w:majority, j:true` answer different questions: "did enough servers see this write" vs. "is this write crash-durable on the ones that did."

### The Task

The script inserts 1,000 documents under four write-concern configurations (`w:1,j:false`; `w:1,j:true`; `w:majority,j:false`; `w:majority,j:true`) and reports average, P50, and P99 latency for each.

Before running it: rank the four configurations from fastest to slowest based on the explanations above, and estimate roughly how much slower `w:majority` will be compared to `w:1` (same order of magnitude? 2x? 10x?). Then compare your ranking and estimate against the actual printed table.

## Activity 2: Simulate a Network Partition [`lab_02_simulate_partition.sh`]

### Topics You Need First

**A partition doesn't mean "the database is down."** It means some replica set members can no longer reach each other. Whether your application *notices* depends entirely on the write concern it's using: with `w:1`, the primary keeps accepting writes locally even if it can't reach a now-unreachable secondary; with `w:majority`, writes will block or fail the moment the primary can no longer reach enough members to form a majority.

**This is the CAP theorem stated as an operational fact, not an abstraction.** During a real partition, you are forced to choose (per-operation, via write concern) between availability (keep accepting writes, `w:1`, possibly losing them if this node never rejoins) and consistency (`w:majority`, refuse to accept writes you can't get acknowledged by a majority, guaranteeing nothing is silently lost).

### The Task

The script disconnects one container from the Docker network the replica set runs on (simulating a partition), waits, checks `rs.status()` to see how the remaining members classify their own state, then reconnects the network and confirms the member rejoins and catches up.

Before running it: predict what you'll see in `rs.status()` while the partition is active -- will the disconnected member still claim to be healthy? Will the *remaining* members still have a primary? Then run it and check your prediction against the actual `stateStr` values printed for each member.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_write_concern_latency.py` | Activity 1 |
| `lab_02_simulate_partition.sh` | Activity 2 |

## Check Your Work

For Activity 1, the correct ordering (fastest to slowest) should be `w:1,j:false` &lt; `w:1,j:true` &lt; `w:majority,j:false` &lt; `w:majority,j:true` -- if your measured numbers come out in a different order, re-run the benchmark (background load on your machine can distort a single run) before assuming the concept is wrong.

For Activity 2, the key thing to verify is asymmetry: the remaining majority of the replica set should still have a working primary and continue accepting writes throughout the simulated partition (this is what "majority" buys you), while the disconnected member's own view of the world (if you could query it directly) would show it unable to reach a primary at all.
