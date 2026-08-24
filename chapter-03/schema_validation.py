"""Schema Validation Demo - JSON Schema validation on MongoDB collections."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, banner


BOOK_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["title", "author", "year", "price", "isbn"],
        "properties": {
            "title": {"bsonType": "string", "minLength": 1, "description": "Book title (required)"},
            "author": {"bsonType": "string", "minLength": 1, "description": "Author name (required)"},
            "year": {"bsonType": "int", "minimum": 1900, "maximum": 2030, "description": "Publication year 1900-2030"},
            "price": {"bsonType": "double", "minimum": 0, "description": "Price must be non-negative"},
            "isbn": {"bsonType": "string", "pattern": r"^\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1}$", "description": "ISBN-13 format"},
            "genre": {"bsonType": "string"},
            "tags": {"bsonType": "array", "items": {"bsonType": "string"}},
        }
    }
}


VALID_DOCS = [
    {"title": "Clean Architecture", "author": "Robert C. Martin", "year": 2017, "price": 39.99, "isbn": "978-0-13-449416-6", "genre": "Software Engineering"},
    {"title": "The Art of War", "author": "Sun Tzu", "year": 2003, "price": 9.99, "isbn": "978-1-59030-227-0", "genre": "Strategy"},
]

INVALID_DOCS = [
    {"title": "No Author Book", "year": 2020, "price": 29.99, "isbn": "978-0-00-000000-0"},  # missing author
    {"title": "Bad Year Book", "author": "Someone", "year": 1800, "price": 10.0, "isbn": "978-0-00-000000-0"},  # year < 1900
    {"title": "Negative Price", "author": "Someone", "year": 2020, "price": -5.0, "isbn": "978-0-00-000000-0"},  # negative price
    {"title": "Bad ISBN", "author": "Someone", "year": 2020, "price": 15.0, "isbn": "NOT-A-VALID-ISBN"},  # bad pattern
]


def main():
    banner("Schema Validation Demo")
    db = get_db("nosql_labs")

    if "books_validated" in db.list_collection_names():
        db.drop_collection("books_validated")
    db.create_collection("books_validated", validator=BOOK_VALIDATOR)
    col = db["books_validated"]
    print("[OK] Created collection with JSON Schema validator.\n")

    # Valid inserts
    print("=== Valid Documents ===")
    for doc in VALID_DOCS:
        try:
            col.insert_one(doc)
            print(f"  [PASS] '{doc['title']}' inserted successfully")
        except Exception as e:
            print(f"  [FAIL] '{doc['title']}': {e.details['errmsg'][:60]}")

    # Invalid inserts
    print("\n=== Invalid Documents (should fail) ===")
    for doc in INVALID_DOCS:
        try:
            col.insert_one(doc)
            print(f"  [UNEXPECTED PASS] '{doc.get('title', 'unknown')}'")
        except Exception as e:
            print(f"  [REJECTED] '{doc.get('title', 'unknown')}': {e.details['errmsg'][:70]}")

    print(f"\n  Total documents in collection: {col.count_documents({})}")
    banner("Schema Validation Demo Complete")


if __name__ == "__main__":
    main()
