#!/bin/bash
# Lab 8.1 - Deploy a Local Replica Set
# Prerequisites: Docker and Docker Compose installed

set -e

echo "======================================="
echo "  Lab 8.1: Deploy Local Replica Set"
echo "======================================="

cd "$(dirname "$0")"

# Step 1: Start containers
echo ""
echo "=== Step 1: Starting 3-node Docker cluster ==="
docker compose -f docker-compose-replicaset.yml up -d
echo "Waiting for containers to be ready..."
sleep 10

# Step 2: Initialize replica set
echo ""
echo "=== Step 2: Initializing replica set rs0 ==="
mongosh --host localhost --port 27017 --eval '
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "host.docker.internal:27017", priority: 2 },
    { _id: 1, host: "host.docker.internal:27018" },
    { _id: 2, host: "host.docker.internal:27019", arbiterOnly: true }
  ]
})
'
echo "Waiting for election (15s)..."
sleep 15

# Step 3: Check status
echo ""
echo "=== Step 3: Replica Set Status ==="
mongosh --host localhost --port 27017 --eval 'rs.status().members.forEach(m => print(m.name, m.stateStr, m.health))'

# Step 4: Verify replication
echo ""
echo "=== Step 4: Verify Replication ==="
mongosh --host localhost --port 27017 --eval '
use testdb;
db.testcollection.insertOne({message: "Hello from replica set!", timestamp: new Date()});
print("Inserted into PRIMARY");
'

echo "Reading from SECONDARY (after 2s)..."
sleep 2
mongosh --host localhost --port 27018 --eval '
rs.secondaryOk();
db.getSiblingDB("testdb").testcollection.find().forEach(d => printjson(d));
'

echo ""
echo "[OK] Replica set is running and replicating."
echo ""
echo "Connection string for PyMongo:"
echo '  uri = "mongodb://host.docker.internal:27017,host.docker.internal:27018,host.docker.internal:27019/?replicaSet=rs0"'
echo ""
echo "To stop: docker compose -f docker-compose-replicaset.yml down"
