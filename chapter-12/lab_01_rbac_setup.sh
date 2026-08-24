#!/bin/bash
# Lab 12.1 - Configure Authentication and RBAC
# Prerequisites: MongoDB running standalone or replica set

set -e

echo "======================================="
echo "  Lab 12.1: Authentication & RBAC Setup"
echo "======================================="

echo ""
echo "=== Step 1: Create Admin User ==="
mongosh --quiet --eval '
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

echo ""
echo "=== Step 2: Create Application Users ==="
mongosh --quiet --eval '
use admin;

// Read-only analyst for reporting
db.createUser({
  user: "analyst",
  pwd: "AnalystPass123!",
  roles: [
    { role: "read", db: "nosql_labs" },
    { role: "read", db: "bookstore" }
  ]
});
print("[OK] Created: analyst (read-only on nosql_labs, bookstore)");

// Read-write app user for nosql_labs only
db.createUser({
  user: "app_writer",
  pwd: "WriterPass123!",
  roles: [
    { role: "readWrite", db: "nosql_labs" }
  ]
});
print("[OK] Created: app_writer (readWrite on nosql_labs)");

// Custom role: can read all but only write to specific collections
db.createRole({
  role: "limitedWriter",
  privileges: [
    { resource: { db: "nosql_labs", collection: "logs" }, actions: ["find", "insert", "update"] },
    { resource: { db: "nosql_labs", collection: "" }, actions: ["find"] }
  ],
  roles: []
});
db.createUser({
  user: "log_writer",
  pwd: "LogPass123!",
  roles: [{ role: "limitedWriter", db: "nosql_labs" }]
});
print("[OK] Created: log_writer (custom role: insert+update on logs, read all)");
'

echo ""
echo "=== Step 3: Test Permission Enforcement ==="
echo "--- analyst trying to write (should FAIL) ---"
mongosh --quiet -u "analyst" -p "AnalystPass123!" --authenticationDatabase admin --eval '
use nosql_labs;
try {
  db.test_col.insertOne({x: 1});
  print("[ERROR] Write should have failed!");
} catch(e) {
  print("[OK] Write correctly rejected: " + e.message.substring(0, 60));
}
'

echo ""
echo "--- app_writer trying to read bookstore (should FAIL) ---"
mongosh --quiet -u "app_writer" -p "WriterPass123!" --authenticationDatabase admin --eval '
try {
  db.getSiblingDB("bookstore").books.find().toArray();
  print("[ERROR] Read should have failed!");
} catch(e) {
  print("[OK] Read correctly rejected: " + e.message.substring(0, 60));
}
'

echo ""
echo "[OK] RBAC setup complete."
echo ""
echo "Next step: Restart MongoDB with --auth flag:"
echo "  mongod --auth --dbpath /data/db"
echo "  Then connect: mongosh -u admin -p 'AdminPass123!' --authenticationDatabase admin"
