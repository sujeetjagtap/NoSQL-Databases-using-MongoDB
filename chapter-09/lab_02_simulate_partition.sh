#!/bin/bash
# Lab 9.2 - Simulate a Network Partition (Design Lab)
set -e
echo "=== Lab 9.2: Network Partition Simulation ==="
echo "Prerequisites: Ch 8 replica set running"
echo ""
echo "Step 1: Find container and network"
CONTAINER=$(docker ps --filter ancestor=mongo:7 --format "{{.Names}}" | head -1)
echo "  Container: $CONTAINER"
NETWORK=$(docker inspect $CONTAINER --format "{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}")
echo "  Network: $NETWORK"
echo ""
echo "Step 2: Baseline write latency (w:1)"
mongosh --quiet --eval "var s=new Date();for(var i=0;i<100;i++){db.test.insertOne({x:i})}print(Baseline w:1: +((new Date()-s))+ms for 100 inserts)"
echo ""
echo "Step 3: Disconnect secondary network"
docker network disconnect $NETWORK $CONTAINER 2>/dev/null || true
echo "  Network disconnected. Waiting 15s..."
sleep 15
echo ""
echo "Step 4: Check replica set state"
mongosh --quiet --eval "rs.status().members.forEach(function(m){print(m.name +  - -
