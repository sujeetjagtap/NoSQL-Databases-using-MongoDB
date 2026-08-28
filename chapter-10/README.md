# Chapter 10: Transactions, Atomicity, and Durability

## What You'll Learn

- How to wrap multiple document writes in a single ACID transaction with PyMongo's session API
- Why a single-document update is already atomic in MongoDB without a transaction, and what a multi-document transaction adds on top of that
- Read concern `"snapshot"` and write concern `"majority"` as the pairing that gives a transaction its actual ACID guarantees
- What happens when concurrent transactions race for the same resource (a write conflict), and how to detect and handle it rather than silently losing an update

## Prerequisites

MongoDB 4.0+ running as at least a single-node replica set (multi-document transactions require replica-set mode, even with only one member -- a plain standalone `mongod` will reject them).

## Activity 1: Implement a Bank Transfer Transaction [`lab_01_bank_transfer.py`]

### Topics You Need First

**Why a bank transfer needs a real transaction, not two separate updates.** Debiting one account and crediting another are two separate documents. If you did them as two independent `update_one()` calls and your process crashed between them, you could debit money without ever crediting it -- money disappears. A transaction guarantees both writes happen together, or neither does.

**Read concern `"snapshot"`.** Inside a transaction, this ensures every read sees a consistent point-in-time view of the data, unaffected by other writes happening concurrently elsewhere in the database -- so the balance check you read at the start of the transaction is still valid by the time you act on it.

**Write concern `"majority"` on the transaction's commit.** This ensures the transaction's combined effect (both the debit and the credit) is durable across a majority of replica set members before your application is told it succeeded -- the same guarantee from Chapter 9, now applied to a multi-document unit of work instead of a single write.

**Retry logic exists because transient errors are expected, not exceptional.** A transaction can fail due to a temporary write conflict with another concurrent transaction, and MongoDB's driver marks such errors as retryable. The correct response is to retry the *whole transaction* from the start (not just the failed operation), which is exactly what the `MAX_RETRIES` loop in this file does.

### The Task

Three accounts are seeded with balances. The script attempts a transfer that includes a balance check (`{"account_id": from_id, "balance": {"$gte": amount}}` -- the query only matches if there's enough money) inside the debit's own `update_one`, so an insufficient-funds transfer fails at the database level rather than needing a separate application-side check-then-act.

Before reading the transaction's error-handling: predict what should happen if you try to transfer more money than an account holds. Then trace through the code to confirm the `matched_count == 0` check is what catches that case, and that it correctly aborts the whole transaction rather than leaving the sender debited with no corresponding credit.

## Activity 2: Inventory Reservation with Transactions [`lab_02_inventory_reservation.py`]

### Topics You Need First

**The classic overselling problem.** If ten customers simultaneously try to buy the last five units of a product, a naive "check stock, then decrement" (as two separate steps) can let more than five reservations succeed, because multiple threads can all read "stock: 5" before any of them writes their decrement. A transaction that reads and writes the stock count as one atomic unit prevents this.

**Concurrent transactions racing for the same document produce write conflicts, by design.** When two transactions try to modify the same document at the same time, MongoDB aborts one of them rather than silently corrupting the data -- this activity is built specifically to make you see that happen, by launching ten concurrent reservation attempts against a stock of only five units.

### The Task

One product is seeded with a stock of 5. Ten Python threads each attempt to reserve exactly one unit, concurrently, each inside its own transaction.

Before running it: predict how many of the ten threads will print `RESERVED` versus `INSUFFICIENT` or `CONFLICT`, and predict the final `stock` value in the database. The correct outcome is exactly 5 successful reservations and a final stock of 0 -- no overselling, and no lost updates -- regardless of the fact that all ten threads started at essentially the same instant.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_bank_transfer.py` | Activity 1 |
| `lab_02_inventory_reservation.py` | Activity 2 |

## Check Your Work

For Activity 1, run at least one transfer that should succeed and one that should fail (insufficient funds) and confirm: after the successful transfer, the sender's and receiver's balances both changed by exactly the transferred amount; after the failed transfer, *neither* account's balance changed at all (not a partial debit).

For Activity 2, the final stock count is the single number that tells you whether the transaction boundary is correct: exactly 0 means every reservation was properly serialized against the real remaining stock. Any other number (especially a negative one) means two threads managed to both read and act on the same stale stock value -- which would mean the check-and-decrement wasn't actually atomic.
