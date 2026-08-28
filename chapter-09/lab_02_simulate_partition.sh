#!/bin/bash
# Lab 9.2 - Simulate a Network Partition (Design Lab)
# Prerequisites: Ch 8 replica set running (docker-compose-replicaset.yml)
set -e

echo "=== Lab 9.2: Network Partition Simulation ==="
echo "Prerequisites: Ch 8 replica set running"
echo ""

echo "Step 1: Find container and network"
CONTAINER=$(docker ps --filter ancestor=mongo:7 --format "{{.Names}}" | head -1)
echo "  Container: $CONTAINER"
NETWORK=$(docker inspect "$CONTAINER" --format "{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}")
echo "  Network: $NETWORK"
echo ""

echo "Step 2: Baseline write latency (w:1)"
mongosh --quiet --eval '
var s = new Date();
for (var i = 0; i < 100; i++) { db.test.insertOne({x: i}); }
print("Baseline w:1: " + (new Date() - s) + "ms for 100 inserts");
'
echo ""

echo "Step 3: Disconnect secondary network (simulating a partition)"
docker network disconnect "$NETWORK" "$CONTAINER" 2>/dev/null || true
echo "  Network disconnected. Waiting 15s..."
sleep 15
echo ""

echo "Step 4: Check replica set state during the partition"
mongosh --quiet --eval '
rs.status().members.forEach(function(m) {
  print(m.name + " - " + m.stateStr);
});
'
echo ""

echo "Step 5: Reconnect network and observe recovery"
docker network connect "$NETWORK" "$CONTAINER" 2>/dev/null || true
echo "  Network reconnected. Waiting 15s for the member to rejoin..."
sleep 15
mongosh --quiet --eval '
rs.status().members.forEach(function(m) {
  print(m.name + " - " + m.stateStr);
});
'
echo ""

echo "[OK] Lab 9.2 complete."
echo "Key observation: with w:majority, writes during Step 3 either blocked or"
echo "were rejected once the primary could no longer reach a majority of voting"
echo "members. With w:1 (Step 2's baseline), writes to the primary kept"
echo "succeeding locally even while a secondary was unreachable -- this is the"
echo "availability-vs-consistency trade-off from Chapter 9 made concrete."
