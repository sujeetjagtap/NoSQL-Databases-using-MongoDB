"""Lab 2.1 - Environment Setup Verification
Check all required tools and connections for the labs."""

import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config.connection import banner
from rich.console import Console
from rich.table import Table

console = Console()


def check_python_version():
    print(f"  Python      : {sys.version.split()[0]}")
    return True


def check_pymongo():
    try:
        import pymongo
        print(f"  PyMongo     : {pymongo.version}")
        return True
    except ImportError:
        print("  PyMongo     : NOT INSTALLED (pip install pymongo)")
        return False


def check_mongo_local():
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        info = client.server_info()
        print(f"  MongoDB Local: {info['version']} [OK]")
        return True
    except (ConnectionFailure, Exception):
        print("  MongoDB Local: NOT RUNNING (docker run -d -p 27017:27017 mongo:7)")
        return False


def check_mongo_atlas():
    atlas_uri = os.getenv("MONGO_URI_ATLAS")
    if not atlas_uri:
        print("  MongoDB Atlas: NOT CONFIGURED (set MONGO_URI_ATLAS in .env)")
        return False
    try:
        client = MongoClient(atlas_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("  MongoDB Atlas: CONNECTED [OK]")
        return True
    except Exception as e:
        print(f"  MongoDB Atlas: FAILED ({e})")
        return False


def check_docker():
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  Docker      : {result.stdout.strip()}")
            # Check if MongoDB container is running
            ps = subprocess.run(["docker", "ps", "--filter", "ancestor=mongo:7", "--format", "{{.Names}}"],
                                capture_output=True, text=True, timeout=5)
            if ps.stdout.strip():
                print(f"  Mongo Container: Running ({ps.stdout.strip()})")
            else:
                print("  Mongo Container: NOT RUNNING")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  Docker      : NOT INSTALLED")
    return False


def check_optional_packages():
    optional = ["fastapi", "streamlit", "voyageai", "neo4j", "cassandra", "rich", "dotenv"]
    for pkg in optional:
        try:
            __import__(pkg)
            print(f"  {pkg:16} : installed")
        except ImportError:
            print(f"  {pkg:16} : not installed (optional)")


def main():
    banner("Lab 2.1: Environment Setup Verification")

    table = Table(title="Environment Checklist", show_lines=True)
    table.add_column("Component", style="cyan", width=20)
    table.add_column("Status", width=50)

    checks = [
        ("Python & PyMongo", check_python_version),
        ("PyMongo Driver", check_pymongo),
        ("MongoDB (Local)", check_mongo_local),
        ("MongoDB Atlas", check_mongo_atlas),
        ("Docker", check_docker),
    ]

    results = {}
    print("Core Components:")
    for name, fn in checks:
        results[name] = fn()

    print("\nOptional Packages:")
    check_optional_packages()

    # Summary
    print("\n--- Summary ---")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"  Core checks passed: {passed}/{total}")
    if passed >= 3:  # At minimum: Python + PyMongo + one MongoDB connection
        print("  [OK] You are ready to start the labs!")
    else:
        print("  [WARN] Some required components are missing. See above for help.")

    banner("Lab 2.1 Complete")


if __name__ == "__main__":
    main()
