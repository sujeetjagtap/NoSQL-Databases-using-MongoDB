#!/bin/bash
# Lab 12.2 - TLS / Encryption-in-Transit Setup
# Prerequisites: MongoDB (mongod, mongosh) and OpenSSL installed locally.
# This lab generates a self-signed CA + server certificate, starts mongod
# with TLS required, and proves that a non-TLS connection is rejected while
# a TLS connection (mongosh and PyMongo) succeeds.

set -e
cd "$(dirname "$0")"

CERT_DIR="./tls"
TLS_PORT=27100

echo "======================================="
echo "  Lab 12.2: TLS / Encryption-in-Transit"
echo "======================================="

# --- Step 1: Generate a self-signed CA and server certificate ---
echo ""
echo "=== Step 1: Generate CA and server certificate ==="
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/mongodb.pem" ]; then
  # Certificate Authority
  openssl req -newkey rsa:2048 -new -x509 -days 365 -nodes \
    -out "$CERT_DIR/ca.crt" -keyout "$CERT_DIR/ca.key" \
    -subj "/CN=NoSQL-Labs-CA" 2>/dev/null
  echo "[OK] Generated CA: $CERT_DIR/ca.crt"

  # Server key + certificate signing request
  openssl req -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" \
    -subj "/CN=localhost" 2>/dev/null

  # Sign the server certificate with our CA
  openssl x509 -req -in "$CERT_DIR/server.csr" \
    -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial \
    -out "$CERT_DIR/server.crt" -days 365 2>/dev/null

  # mongod expects the key and certificate concatenated into a single PEM
  cat "$CERT_DIR/server.key" "$CERT_DIR/server.crt" > "$CERT_DIR/mongodb.pem"
  chmod 600 "$CERT_DIR/mongodb.pem"
  echo "[OK] Generated server certificate: $CERT_DIR/mongodb.pem"
else
  echo "[OK] Certificates already exist in $CERT_DIR (delete the folder to regenerate)"
fi

# --- Step 2: Start mongod with TLS required ---
echo ""
echo "=== Step 2: Start mongod with --tlsMode requireTLS ==="
echo "Run this in a separate terminal (leave it running):"
echo ""
echo "  mongod --dbpath /data/db --port $TLS_PORT \\"
echo "    --tlsMode requireTLS \\"
echo "    --tlsCertificateKeyFile $CERT_DIR/mongodb.pem \\"
echo "    --tlsCAFile $CERT_DIR/ca.crt"
echo ""
read -p "Press Enter once mongod is running with the flags above... " _

# --- Step 3: Confirm a non-TLS connection is rejected ---
echo ""
echo "=== Step 3: Connect WITHOUT TLS (expected: connection refused) ==="
if mongosh --quiet --port "$TLS_PORT" --eval 'db.runCommand({ping:1})' >/tmp/tls_lab_notls.log 2>&1; then
  echo "[UNEXPECTED] Non-TLS connection succeeded -- check that --tlsMode requireTLS is set."
  cat /tmp/tls_lab_notls.log
else
  echo "[OK] Non-TLS connection was correctly rejected."
fi

# --- Step 4: Confirm a TLS connection succeeds (mongosh) ---
echo ""
echo "=== Step 4: Connect WITH TLS via mongosh (expected: success) ==="
mongosh --quiet --port "$TLS_PORT" \
  --tls --tlsCAFile "$CERT_DIR/ca.crt" --tlsAllowInvalidHostnames \
  --eval '
db.runCommand({ping: 1});
print("[OK] mongosh connected over TLS.");
'

# --- Step 5: Confirm a TLS connection succeeds (PyMongo) ---
echo ""
echo "=== Step 5: Connect WITH TLS via PyMongo (expected: success) ==="
python3 - "$CERT_DIR/ca.crt" "$TLS_PORT" <<'PYEOF'
import sys
from pymongo import MongoClient
from pymongo.errors import PyMongoError

ca_file, port = sys.argv[1], sys.argv[2]
uri = f"mongodb://localhost:{port}/?tls=true&tlsCAFile={ca_file}&tlsAllowInvalidHostnames=true"

client = MongoClient(uri, serverSelectionTimeoutMS=5000)
try:
    client.admin.command("ping")
    print("[OK] PyMongo connected over TLS.")
except PyMongoError as e:
    print(f"[ERROR] PyMongo TLS connection failed: {e}")
finally:
    client.close()
PYEOF

echo ""
echo "[OK] Lab 12.2 complete."
echo ""
echo "In production:"
echo "  - Use a certificate issued by a trusted internal or public CA, not a"
echo "    self-signed one (self-signed certs are for local/lab use only)."
echo "  - Never commit the CA key, server key, or mongodb.pem to version control."
echo "  - Set a certificate expiry/rotation reminder well before the 365-day mark."
echo "  - Combine this with the RBAC setup from Lab 12.1: TLS protects data in"
echo "    transit, RBAC controls what an authenticated connection can do."
