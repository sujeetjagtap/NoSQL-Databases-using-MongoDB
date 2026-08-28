"""Lab 7.1 - Analyze a Production Schema

Embed vs reference analysis with $bsonSize.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner, print_json
from rich.table import Table
from rich.console import Console

console = Console()


BLOG_POSTS = [
    {
        "title": "Getting Started with MongoDB",
        "author": "arjun", "slug": "getting-started-mongodb",
        "tags": ["mongodb", "nosql", "beginner"],
        "comments": [
            {"author": "reader1", "text": "Great intro!", "created": "2024-01-16"},
            {"author": "reader2", "text": "More on aggregation please", "created": "2024-01-17"},
        ]
    },
    {
        "title": "Advanced Aggregation Pipelines",
        "author": "sneha", "slug": "advanced-aggregation",
        "tags": ["mongodb", "aggregation", "intermediate"],
        "comments": [
            {"author": "reader1", "text": "$facet is amazing", "created": "2024-02-01"},
            {"author": "reader3", "text": "Very well explained", "created": "2024-02-02"},
            {"author": "reader4", "text": "Bookmarking this", "created": "2024-02-03"},
        ]
    },
    {
        "title": "Vector Search with MongoDB Atlas",
        "author": "kavya", "slug": "vector-search-atlas",
        "tags": ["mongodb", "ai", "vector-search", "advanced"],
        "comments": [
            {"author": "reader5", "text": "When is IVF better than HNSW?", "created": "2024-03-01"},
        ]
    },
]


def main():
    banner("Lab 7.1: Analyze a Production Schema")
    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "blog_posts")
    col.insert_many(BLOG_POSTS)

    # Calculate document sizes
    print("=== Document Size Analysis ($bsonSize) ===")
    table = Table(title="Blog Post Document Sizes")
    table.add_column("Post", style="cyan", width=35)
    table.add_column("Comments", justify="right")
    table.add_column("BSON Size (bytes)", justify="right")
    table.add_column("Pattern", style="green")

    for post in col.find():
        size_result = db.command("bsonsize", post)
        size = size_result["size"]
        table.add_row(
            post["title"][:35],
            str(len(post["comments"])),
            str(size),
            "Embedded comments" if len(post["comments"]) <= 5 else "Consider referencing"
        )
    console.print(table)

    # Analyze embed vs reference patterns
    print("\n=== Embed vs Reference Pattern Analysis ===")
    print(f"  Average comments per post: {sum(len(p['comments']) for p in BLOG_POSTS) / len(BLOG_POSTS):.1f}")
    print(f"  Max comments: {max(len(p['comments']) for p in BLOG_POSTS)}")
    print(f"  Min comments: {min(len(p['comments']) for p in BLOG_POSTS)}")
    print()
    print("  Recommendation:")
    print("  - Comments < 100 per post -> EMBED (fewer queries, faster reads)")
    print("  - Comments > 100 per post -> REFERENCE (avoid 16MB doc limit)")
    print("  - Comments > 1000 per post -> PAGINATED REFERENCE (bucket pattern)")

    # Demonstrate $bsonSize with a large document
    print("\n=== Simulating Large Document Growth ===")
    big_post = {"title": "Popular Post", "author": "celebrity"}
    big_post["comments"] = [{"author": f"user{i}", "text": f"Comment number {i}"} for i in range(100)]
    size_100 = db.command("bsonsize", big_post)["size"]
    print(f"  100 comments  -> {size_100:>8} bytes")

    big_post["comments"] = [{"author": f"user{i}", "text": f"Comment number {i}"} for i in range(1000)]
    size_1k = db.command("bsonsize", big_post)["size"]
    print(f"  1,000 comments -> {size_1k:>8} bytes")

    big_post["comments"] = [{"author": f"user{i}", "text": f"Comment number {i}"} for i in range(10000)]
    size_10k = db.command("bsonsize", big_post)["size"]
    print(f"  10,000 comments -> {size_10k:>8,} bytes")
    print(f"  16 MB limit     -> {16*1024*1024:>8,} bytes")
    if size_10k > 16 * 1024 * 1024:
        print(f"  [WARN] 10K comments EXCEEDS 16MB limit!")

    banner("Lab 7.1 Complete")


if __name__ == "__main__":
    main()