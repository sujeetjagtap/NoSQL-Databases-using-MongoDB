"""BSON Type Exploration - Understand BSON types in MongoDB."""

import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from bson import Binary, Int64, Regex, ObjectId
from config.connection import get_db, reset_collection, banner, print_json


def main():
    banner("BSON Type Exploration")

    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "bson_types")

    # Document showcasing every BSON type
    doc = {
        "_id": ObjectId(),
        "string_field": "Hello, BSON!",
        "int32_field": 42,
        "int64_field": Int64(9223372036854775807),
        "double_field": 3.14159,
        "boolean_field": True,
        "null_field": None,
        "datetime_field": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        "binary_field": Binary(b'\x48\x65\x6c\x6c\x6f', subtype=0),  # "Hello" as bytes
        "regex_field": Regex(r'^[A-Z][a-z]+$', 'i'),
        "array_field": ["MongoDB", "Cassandra", "Neo4j"],
        "embedded_doc": {
            "name": "NoSQL",
            "year_founded": 2009,
            "features": ["schema-flexible", "horizontal-scale"]
        },
        "timestamp_field": datetime.now(timezone.utc),
    }

    col.insert_one(doc)
    print("[OK] Inserted document with multiple BSON types.\n")

    # Read back and display types
    retrieved = col.find_one()
    print("Field Type Analysis:")
    print("-" * 50)
    type_map = {
        "string_field": "BSON String",
        "int32_field": "BSON Int32",
        "int64_field": "BSON Int64",
        "double_field": "BSON Double",
        "boolean_field": "BSON Boolean",
        "null_field": "BSON Null",
        "datetime_field": "BSON DateTime",
        "binary_field": "BSON Binary",
        "regex_field": "BSON Regex",
        "array_field": "BSON Array",
        "embedded_doc": "BSON Embedded Document",
    }
    for field, bson_desc in type_map.items():
        val = retrieved[field]
        py_type = type(val).__name__
        print(f"  {field:20} -> Python: {py_type:20} | BSON: {bson_desc}")

    # Size demonstration
    import bson
    doc_bytes = bson.BSON.encode(retrieved)
    print(f"\n  Document BSON size: {len(doc_bytes)} bytes")
    print(f"  (Max BSON document size: 16 MB = {16 * 1024 * 1024} bytes)")

    banner("BSON Exploration Complete")


if __name__ == "__main__":
    main()
