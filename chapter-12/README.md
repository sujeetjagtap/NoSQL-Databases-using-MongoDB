# Chapter 12: Database Security and the CIA Triad

## What You'll Learn

- How the CIA triad (Confidentiality, Integrity, Availability) applies concretely to a database, not just as an abstract security framework
- Role-Based Access Control (RBAC): built-in roles, custom roles, and the principle of least privilege
- TLS/encryption-in-transit: what it protects against and how to verify it's actually enforced, not just configured
- Field-level redaction via views: how to expose a restricted, masked version of sensitive data without duplicating the underlying collection

## Prerequisites

MongoDB running locally, `mongosh` installed. Activity 2 additionally needs OpenSSL installed locally.

## Activity 1: Configure Authentication and RBAC [`lab_01_rbac_setup.sh`]

### Topics You Need First

**Confidentiality starts with "who is allowed to do what," not encryption.** RBAC is MongoDB's confidentiality control: every user gets one or more roles, and every role grants a specific, scoped set of actions on a specific set of resources. The default posture should be least privilege -- grant exactly what a user needs, nothing more, rather than a small number of all-powerful accounts.

**Built-in vs. custom roles.** MongoDB ships broad built-in roles (`read`, `readWrite`, `readWriteAnyDatabase`, `clusterAdmin`, etc.) scoped to a whole database or the whole cluster. When that granularity isn't fine enough -- for example, "can insert and update the `logs` collection specifically, and read everything else, but write nothing else" -- you define a custom role listing exact `resource`/`actions` pairs, as this script does for `limitedWriter`.

**A permission you haven't tested is a permission you don't actually know you have.** It's easy to define a role and assume it works. This activity doesn't stop at creating users -- it authenticates *as* those restricted users and attempts an action they should be denied, to prove the restriction is real rather than just declared.

### The Task

The script creates an admin user, then three progressively more restricted users: a read-only `analyst` (scoped to two specific databases), a `readWrite` `app_writer` (scoped to one database only), and a `log_writer` using a custom role that can only insert/update one specific collection while reading everything else.

Before reading Step 3: predict which of the two tested actions (`analyst` writing to `nosql_labs`, `app_writer` reading from `bookstore`) should fail, and why, based purely on the roles granted in Step 2. Then check the script's own `[OK] ... correctly rejected` output to confirm your prediction.

## Activity 2: TLS / Encryption-in-Transit Setup [`lab_02_tls_setup.sh`]

### Topics You Need First

**TLS is a different confidentiality control from RBAC, protecting a different attack surface.** RBAC controls what an *authenticated* connection is allowed to do. TLS controls whether the data flowing over the network between your application and MongoDB can be read by someone intercepting the traffic in between -- a concern RBAC does nothing about, since RBAC only matters once a connection is already established.

**A self-signed certificate is for labs and local dev, not production.** This activity generates its own CA and server certificate with OpenSSL specifically so you can see the mechanics without needing a certificate from a real CA. In production, you'd use a certificate issued by a trusted internal or public CA instead -- the mechanics of enabling TLS on `mongod` are otherwise identical.

**Proving TLS is enforced, not just configured, means testing the negative case.** It's not enough to confirm a TLS connection *succeeds* -- you have to also confirm a *non*-TLS connection is actually *rejected* once `--tlsMode requireTLS` is set. A misconfigured server that still silently accepts plaintext connections has bought you nothing.

### The Task

The script generates a self-signed CA and server certificate, walks you through starting `mongod` with `--tlsMode requireTLS`, then attempts two connections: one without TLS (which should be refused) and one with TLS via both `mongosh` and PyMongo (which should succeed).

Before running Steps 3 and 4: predict what error you'd expect to see from the non-TLS connection attempt, and confirm your prediction matches what actually gets printed.

## Activity 3: Field-Level Redaction via Views [`rbac_field_redaction.py`]

### Topics You Need First

**Redaction is a confidentiality control that works *within* a role someone already has.** RBAC (Activity 1) controls access at the collection level -- a role either can or can't read a collection at all. But sometimes you want a user to see *most* fields of a document while a few sensitive ones (a salary, a full SSN) stay hidden or masked. A MongoDB view built with an aggregation pipeline lets you define exactly that: a read-only, derived "collection" that always applies the same field-level transformation.

**`$$REMOVE` and partial masking are two different redaction strategies.** Setting a field's projected value to the special `$$REMOVE` variable drops it from the output entirely (used here for `salary`). Partially masking a field (used here for `ssn`, keeping only the last 4 digits visible via `$substr` and `$concat`) preserves some utility of the field -- e.g., confirming an SSN's last four digits match a support request -- without exposing the whole value.

### The Task

Employee records (including full SSN and salary) are seeded. The script prints the full documents (the "admin view"), then creates a view (`employees_safe`) that masks the SSN to only its last four digits and removes `salary` entirely, and prints the same records through that view.

Before creating the view yourself (or reading how the script does it): write the `$project` stage you'd use to keep `username`/`email`/`role` untouched, mask `ssn` to `***-**-1234` format, and drop `salary` completely. Then compare your pipeline against the one in the source.

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_rbac_setup.sh` | Activity 1 |
| `lab_02_tls_setup.sh` | Activity 2 |
| `rbac_field_redaction.py` | Activity 3 |

## Check Your Work

For Activity 1, both restricted-user test cases in Step 3 should print `[OK] ... correctly rejected` -- if either one instead prints `[ERROR] ... should have failed!`, the role definition granted more than intended and needs to be tightened.

For Activity 2, the non-TLS connection attempt in Step 3 should fail outright, and both the `mongosh` and PyMongo TLS connections in Steps 4-5 should print `[OK] ... connected over TLS.`

For Activity 3, compare the two printed sections directly: the admin view should show full SSNs and salaries, while the `employees_safe` view should show every SSN ending in the same masked prefix (`***-**-`) and no `salary` key at all in any of the three records.
