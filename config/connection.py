"""
Shared MongoDB connection utility for all lab scripts.

Usage:
    from config.connection import get_client, get_db, close_client

    client = get_client()
    db = get_db("nosql_labs")
    # ... do work ...
    close_client()
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_client: MongoClient | None = None


def get_client(uri: str | None = None) -> MongoClient:
    """Return a singleton MongoClient. Reuses existing connection if available."""
    global _client
    if _client is None:
        connection_uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        _client = MongoClient(connection_uri, serverSelectionTimeoutMS=5000)
        # Force connection to raise errors early
        _client.admin.command("ping")
        print(f"[OK] Connected to MongoDB at {connection_uri}")
    return _client


def get_db(db_name: str | None = None) -> "pymongo.database.Database":
    """Return a database handle."""
    client = get_client()
    name = db_name or os.getenv("MONGO_DB", "nosql_labs")
    return client[name]


def close_client():
    """Close the singleton connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        print("[OK] MongoDB connection closed.")


def reset_collection(db_name: str, collection_name: str):
    """Drop and recreate a collection (useful for lab restarts)."""
    db = get_db(db_name)
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)
        print(f"[OK] Dropped collection: {db_name}.{collection_name}")
    return db[collection_name]


def print_json(data) -> None:
    """Pretty-print a document or list of documents."""
    from bson import json_util
    import json
    print(json.dumps(data, indent=2, default=json_util.default))


def banner(text: str, char: str = "=", width: int = 60) -> None:
    """Print a section banner."""
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)
    print()
