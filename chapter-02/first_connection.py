"""First Connection - Verify MongoDB connectivity and print server info."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config.connection import banner


def main():
    banner("First Connection to MongoDB")

    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    print(f"Connecting to: {uri}")

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("[OK] Connection successful!\n")

        # Server info
        info = client.server_info()
        print(f"MongoDB Version : {info['version']}")
        print(f"Platform        : {info.get('platform', 'N/A')}")
        print(f"Process ID      : {info.get('pid', 'N/A')}")

        # List databases
        print("\nDatabases:")
        for db_name in client.list_database_names():
            db = client[db_name]
            collections = db.list_collection_names()
            print(f"  {db_name:20} ({len(collections)} collections)")

        print("\n[OK] Environment is ready for lab exercises.")
    except ConnectionFailure as e:
        print(f"[ERROR] Could not connect to MongoDB: {e}")
        print("Make sure MongoDB is running:")
        print("  Docker:  docker run -d -p 27017:27017 --name mongo mongo:7")
        print("  Atlas:   Set MONGO_URI_ATLAS in .env")


if __name__ == "__main__":
    main()
