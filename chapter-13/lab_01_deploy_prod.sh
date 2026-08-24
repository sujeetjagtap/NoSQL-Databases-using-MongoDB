#!/bin/bash
# Lab 13.1 - Deploy a Production Replica Set with Docker Compose
# Includes keyFile authentication

set -e
cd "$(dirname "$0")"

echo "======================================="
echo "  Lab 13.1: Production Replica Set Deployment"
echo "======================================="

# Step 1: Generate keyfile
echo ""
echo "=== Step 1: Generate keyfile ==="
if [ ! -f keyfile ]; then
  openssl rand -base64 756 > keyfile
  chmod 400 keyfile
  echo "[OK] Generated keyfile (756 bytes)"
else
  echo "[OK] keyfile already exists"
fi

# Step 2: Start containers
echo ""
echo "=== Step 2: Starting production containers ==="
docker compose -f docker-compose-production.yml up -d
echo "Waiting for containers..."
sleep 10

# Step 3: Create admin user (first time, before auth is enforced by replset)
echo ""
echo "=== Step 3: Creating admin user ==="
mongosh --quiet --port 27017 --eval '
use admin;
db.createUser({
  user: "admin",
  pwd: "AdminPass123!",
  roles: [
    { role: "userAdminAnyDatabase", db: "admin" },
    { role: "clusterAdmin", db: "admin" },
    { role: "readWriteAnyDatabase", db: "admin" }
  ]
});
print("[OK] Admin user created.");
'

# Step 4: Initiate replica set
echo ""
echo "=== Step 4: Initiating replica set ==="
mongosh --quiet -u admin -p 'AdminPass123!' --authenticationDatabase admin --port 27017 --eval '
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "host.docker.internal:27017", priority: 2 },
    { _id: 1, host: "host.docker.internal:27018" },
    { _id: 2, host: "host.docker.internal:27019", arbiterOnly: true }
  ]
});
print("[OK] Replica set initiated.");
'
echo "Waiting for election..."
sleep 15

# Step 5: Verify
echo ""
echo "=== Step 5: Verify Health ==="
mongosh --quiet -u admin -p 'AdminPass123!' --authenticationDatabase admin --port 27017 --eval '
rs.status().members.forEach(m => print(m.name, m.stateStr));
'

echo ""
echo "[OK] Production replica set is ready."
echo "Connection string (with auth):"
echo '  mongodb://admin:AdminPass123!@host.docker.internal:27017,host.docker.internal:27018,host.docker.internal:27019/admin?replicaSet=rs0&authSource=admin'
echo ""
echo "To stop: docker compose -f docker-compose-production.yml down -v"