"""Lab 2.2 - Bookstore CRUD Operations
Basic Create, Read, Update, Delete with PyMongo."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner, print_json
from rich.console import Console

console = Console()


BOOKS = [
    {"title": "The Pragmatic Programmer", "author": "David Thomas & Andrew Hunt",
     "year": 2019, "genre": "Software Engineering", "price": 49.99, "isbn": "978-0135957059",
     "tags": ["programming", "career", "best-practices"],
     "publisher": {"name": "Addison-Wesley", "location": "Boston"}},
    {"title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann",
     "year": 2017, "genre": "Databases", "price": 45.99, "isbn": "978-1449373320",
     "tags": ["databases", "distributed-systems", "architecture"],
     "publisher": {"name": "O'Reilly Media", "location": "Sebastopol"}},
    {"title": "Deep Learning", "author": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
     "year": 2016, "genre": "Machine Learning", "price": 72.00, "isbn": "978-0262035613",
     "tags": ["AI", "neural-networks", "theory"],
     "publisher": {"name": "MIT Press", "location": "Cambridge"}},
    {"title": "Clean Code", "author": "Robert C. Martin",
     "year": 2008, "genre": "Software Engineering", "price": 39.99, "isbn": "978-0132350884",
     "tags": ["programming", "clean-code", "refactoring"],
     "publisher": {"name": "Prentice Hall", "location": "Upper Saddle River"}},
    {"title": "Hands-On Machine Learning", "author": "Aurelien Geron",
     "year": 2022, "genre": "Machine Learning", "price": 59.99, "isbn": "978-1098125974",
     "tags": ["AI", "scikit-learn", "tensorflow", "practical"],
     "publisher": {"name": "O'Reilly Media", "location": "Sebastopol"}},
]


def main():
    banner("Lab 2.2: Bookstore CRUD Operations")
    db = get_db("bookstore")
    col = reset_collection("bookstore", "books")

    # --- CREATE ---
    print("=== CREATE: Inserting 5 books ===")
    result = col.insert_many(BOOKS)
    print(f"[OK] Inserted {len(result.inserted_ids)} books")
    print(f"  IDs: {[str(_id)[:8] + '...' for _id in result.inserted_ids]}")

    # --- READ: Filter by year > 2020 ---
    print("\n=== READ: Books published after 2020 ===")
    recent = list(col.find({"year": {"$gt": 2020}}, {"title": 1, "year": 1, "price": 1, "_id": 0}))
    for b in recent:
        print(f"  {b['title']:<45} ({b['year']}) - ${b['price']:.2f}")

    # --- READ: Filter by genre ---
    print("\n=== READ: Machine Learning books ===")
    ml_books = col.find({"genre": "Machine Learning"}, {"title": 1, "author": 1, "_id": 0})
    for b in ml_books:
        print(f"  {b['title']:<45} by {b['author']}")

    # --- READ: Price range ---
    print("\n=== READ: Books priced $40-$60 ===")
    mid_range = col.find({"price": {"$gte": 40, "$lte": 60}}, {"title": 1, "price": 1, "_id": 0})
    for b in mid_range:
        print(f"  {b['title']:<45} ${b['price']:.2f}")

    # --- READ: Tags search ---
    print("\n=== READ: Books tagged 'AI' ===")
    ai_books = col.find({"tags": "AI"}, {"title": 1, "tags": 1, "_id": 0})
    for b in ai_books:
        print(f"  {b['title']:<45} tags: {b['tags']}")

    # --- UPDATE: Increase prices by 10% ---
    print("\n=== UPDATE: 10% price increase ===")
    before = {b["title"]: b["price"] for b in col.find({}, {"title": 1, "price": 1, "_id": 0})}
    update_result = col.update_many({}, {"$mul": {"price": 1.10}})
    print(f"[OK] Updated {update_result.modified_count} books")
    after = {b["title"]: b["price"] for b in col.find({}, {"title": 1, "price": 1, "_id": 0})}
    for title, old_price in before.items():
        new_price = after[title]
        print(f"  {title:<45} ${old_price:.2f} -> ${new_price:.2f}")

    # --- DELETE: Remove one book ---
    print("\n=== DELETE: Removing 'Clean Code' ===")
    del_result = col.delete_one({"title": "Clean Code"})
    print(f"[OK] Deleted {del_result.deleted_count} document(s)")
    print(f"  Remaining books: {col.count_documents({})}")

    # Final state
    print("\n=== Final Collection State ===")
    for b in col.find({}, {"_id": 0}):
        print(f"  {b['title']}")

    banner("Lab 2.2 Complete")


if __name__ == "__main__":
    main()
