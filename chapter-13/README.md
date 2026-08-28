# Chapter 13: Deploying MongoDB with Containers and the Cloud

## What You'll Learn

- How a "production-shaped" replica set deployment differs from Chapter 8's local one: keyFile authentication instead of no auth at all, an admin user created before the replica set is even initiated
- Kubernetes StatefulSets: stable per-pod network identity and per-pod persistent storage, and why that's specifically what a stateful workload like MongoDB needs that a plain Deployment doesn't provide
- Infrastructure-as-code with Terraform: declaring a MongoDB Atlas project, cluster, and database user as version-controlled configuration instead of manual clicks in a UI
- The specific difference each deployment target (Docker Compose, Kubernetes, Atlas) makes to how a replica set forms and recovers

## Prerequisites

Docker and Docker Compose (Activity 1). Kubernetes is optional for Activity 2 -- `kubectl` and a cluster (minikube, kind, or managed) if you want to actually apply the generated manifests, though the activity is still worthwhile without one. Terraform and a MongoDB Atlas account with API keys, if you want to actually provision the `main.tf` configuration referenced from this chapter.

## Activity 1: Deploy a Production Replica Set with Docker Compose [`lab_01_deploy_prod.sh`]

### Topics You Need First

**keyFile authentication is how replica set members trust each other, not how your application authenticates.** Every member of the replica set shares the same keyfile (a random secret) and uses it to verify that its peers are legitimate members of the same set, not an attacker's rogue `mongod` trying to join the cluster. This is separate from -- and in addition to -- the RBAC user accounts from Chapter 12 that control what *your application* is allowed to do.

**Order of operations matters here in a way it didn't in Chapter 8.** This script creates the admin user *before* initiating the replica set, while auth is still effectively unenforced on a lone, not-yet-clustered node. Once the replica set is initiated and members start requiring keyFile-authenticated connections to each other, you need that admin account already in place to manage the cluster going forward.

### The Task

Run this script to deploy the same logical 3-node replica set as Chapter 8, but with a generated keyfile and an admin user created up front. Compare its steps directly against Chapter 8's `lab_01_deploy_replicaset.sh`.

Before running it, list every difference you can spot between this script and Chapter 8's version just by reading both side by side -- then confirm your list is complete by checking the "Connection string" the script prints at the end, and noticing it now requires a username, password, and `authSource=admin` where Chapter 8's did not.

## Activity 2: Kubernetes StatefulSet for MongoDB [`lab_02_k8s_statefulset.py`]

### Topics You Need First

**Why a plain Kubernetes Deployment is the wrong tool for a replica set.** A Deployment's pods are interchangeable and get a new random identity every time they restart -- fine for stateless web servers, but wrong for a replica set, where each member's identity (hostname) is baked into `rs.status()`'s configuration. A StatefulSet instead gives each pod a stable, predictable name (`mongo-0`, `mongo-1`, `mongo-2`) that survives restarts.

**A headless Service is what makes those stable names actually reachable.** Setting `clusterIP: None` on the Service tells Kubernetes not to load-balance across the pods, but instead to give each one its own individually-addressable DNS name (`mongo-0.mongo.<namespace>.svc.cluster.local`) -- exactly what a replica set's member list needs to point at.

**`volumeClaimTemplates` gives each pod its own persistent disk, not a shared one.** Unlike a single `volumes:` entry (which all pods would share), a `volumeClaimTemplates` block causes Kubernetes to provision a separate `PersistentVolumeClaim` per pod (`mongo-data-mongo-0`, `mongo-data-mongo-1`, ...) -- so a pod rescheduled onto a different node still finds *its own* data waiting for it, not another member's.

### The Task

Running this script generates four Kubernetes manifests (a Namespace, a headless Service, the StatefulSet itself with readiness/liveness probes, and a one-shot Job to call `rs.initiate()` once the pods are up). If `kubectl` is available and pointed at a live cluster, it applies them and waits for the rollout; otherwise it stops after generating the manifests so you can still read them.

Before reading the generated `02-statefulset.yaml`: predict what `serviceName` field the StatefulSet needs to reference for the stable pod-naming to work, and what would break if it referenced the wrong Service (or none at all).

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_deploy_prod.sh` | Activity 1 |
| `docker-compose-production.yml` | The replica set definition used by Activity 1 |
| `lab_02_k8s_statefulset.py` | Activity 2 (generates manifests into a `k8s/` subfolder when run) |
| `main.tf` | Terraform configuration provisioning a MongoDB Atlas project, free-tier (M0) cluster, database user, and IP access list -- referenced by this chapter's cloud-provisioning discussion; run `terraform init && terraform plan` (with `atlas_org_id` and `atlas_user_password` variables set) to see the plan without needing to actually apply it |

## Check Your Work

For Activity 1, the replica set should reach the same healthy 3-member state as Chapter 8's version, but every `mongosh` command against it now requires `-u admin -p ...  --authenticationDatabase admin` -- if you can still connect with no credentials at all, keyFile auth isn't actually being enforced and something in the compose file or the `mongod` startup flags needs to be checked.

For Activity 2, if you have a cluster available, a fully successful run ends with `kubectl exec ... -- mongosh --eval 'rs.status()'` showing all three `mongo-N` pods as healthy members. Without a cluster, success is being able to read the four generated YAML files and correctly identify, for each one, what would break if that specific manifest were missing.
