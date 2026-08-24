"""Lab 3.2 - Migrate from Referenced to Embedded Design
Compare referenced (normalized) vs embedded (denormalized) patterns.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner, print_json
from bson import ObjectId


def main():
    banner("Lab 3.2: Embed vs Reference Migration")
    db = get_db("nosql_labs")

    # ===== PART A: REFERENCED DESIGN =====
    print("=== PART A: Referenced Design (Normalized) ===")
    posts_col = reset_collection("nosql_labs", "posts")
    comments_col = reset_collection("nosql_labs", "comments")

    # Insert 5 posts
    posts = [
        {"title": "Why NoSQL Matters for AI", "author": "arjun", "tags": ["nosql", "ai"], "created": "2024-01-15"},
        {"title": "MongoDB Aggregation Tips", "author": "sneha", "tags": ["mongodb", "aggregation"], "created": "2024-01-20"},
        {"title": "Vector Search Deep Dive", "author": "kavya", "tags": ["vector", "ai", "search"], "created": "2024-02-01"},
        {"title": "CAP Theorem Explained", "author": "arjun", "tags": ["cap", "distributed"], "created": "2024-02-10"},
        {"title": "Graph Databases for Fraud", "author": "rahul", "tags": ["neo4j", "fraud", "graph"], "created": "2024-02-15"},
    ]
    post_result = posts_col.insert_many(posts)
    post_ids = post_result.inserted_ids
    print(f"  Inserted {len(post_ids)} posts")

    # Insert 3 comments per post (15 total)
    comment_data = [
        ["Great overview!", "reader1"], ["I prefer SQL though", "reader2"], ["Bookmarked this", "reader3"],
        ["The $lookup stage is powerful", "reader4"], ["Can you cover $facet next?", "reader1"], ["Very practical", "reader5"],
        ["HNSW vs IVF comparison?", "reader6"], ["How does this scale?", "reader2"], ["Excellent writeup", "reader4"],
        ["AP systems are underrated", "reader7"], ["Good for interviews too", "reader3"], ["Real examples please", "reader5"],
        ["Neo4j Cypher is intuitive", "reader8"], ["Graph + Vector hybrid?", "reader6"], ["Case study needed", "reader7"],
    ]
    comments = []
    for i, post_id in enumerate(post_ids):
        for j in range(3):
            text, author = comment_data[i * 3 + j]
            comments.append({"post_id": post_id, "text": text, "author": author})
    comments_col.insert_many(comments)
    print(f"  Inserted {len(comments)} comments")

    # To get a post with all comments (referenced): need $lookup OR 2 queries
    print("\n  --- Referenced: Getting post + comments requires $lookup ---")
    pipeline = [
        {"$match": {"_id": post_ids[0]}},
        {"$lookup": {"from": "comments", "localField": "_id", "foreignField": "post_id", "as": "comments"}}
    ]
    result = list(posts_col.aggregate(pipeline))
    print(f"  Post: {result[0]['title']} -> {len(result[0]['comments'])} comments")
    ref_query_count = 1  # aggregation pipeline = 1 query

    # ===== PART B: EMBEDDED DESIGN =====
    print("\n=== PART B: Embedded Design (Denormalized) ===")
    embedded_col = reset_collection("nosql_labs", "posts_embedded")

    embedded_posts = []
    for i, post in enumerate(posts):
        post_comments = comment_data[i * 3:(i + 1) * 3]
        embedded_posts.append({
            **post,
            "comments": [{"text": text, "author": author} for text, author in post_comments]
        })
    embedded_col.insert_many(embedded_posts)
    print(f"  Inserted {len(embedded_posts)} embedded posts")

    # To get post with comments: single find, no join
    print("\n  --- Embedded: Getting post + comments is a single find ---")
    embedded_result = embedded_col.find_one({"_id": embedded_col.find()[0]["_id"]})
    print(f"  Post: {embedded_result['title']} -> {len(embedded_result['comments'])} comments")
    emb_query_count = 1

    # ===== COMPARISON =====
    print("\n=== Design Comparison ===")
    print(f"  Referenced: {ref_query_count} query (with $lookup) to get post + comments")
    print(f"  Embedded:   {emb_query_count} query (simple find) to get post + comments")
    print()
    print(f"  {'Aspect':<25} {'Referenced':<25} {'Embedded':<25}")
    print(f"  {'-'*75}")
    print(f"  {'Query simplicity':<25} {'Needs $lookup':<25} {'Single find()':<25}")
    print(f"  {'Data consistency':<25} {'Single source of truth':<25} {'May have duplicates':<25}")
    print(f"  {'Update cost':<25} {'Update 1 doc':<25} {'Update parent + children':<25}")
    print(f"  {'Read performance':<25} {'Slower (join)':<25} {'Faster (no join)':<25}")
    print(f"  {'Best when':<25} {'Comments >> 1K':<25} {'Comments < 100':<25}")

    banner("Lab 3.2 Complete")


if __name__ == "__main__":
    main()