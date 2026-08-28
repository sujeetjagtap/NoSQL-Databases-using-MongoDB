"""Lab 14.1 - Build a Monitoring Dashboard

Retrieve metrics, format as table, log to file, threshold alerts.
"""

import sys, os, time, json, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from config.connection import banner
from rich.table import Table
from rich.console import Console
from datetime import datetime

console = Console()

# Set up logging (relative to this script's own directory, so it works
# regardless of where the repo is cloned or which directory it's run from)
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "metrics.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)


def get_metrics(client):
    """Collect key MongoDB metrics."""
    status = client.admin.command("serverStatus")
    wt = status.get("wiredTiger", {}).get("cache", {})
    connections = status.get("connections", {})
    opcounters = status.get("opcounters", {})

    return {
        "timestamp": datetime.now().isoformat(),
        "connections_current": connections.get("current", 0),
        "connections_available": connections.get("available", 0),
        "op_insert": opcounters.get("insert", 0),
        "op_query": opcounters.get("query", 0),
        "op_update": opcounters.get("update", 0),
        "op_delete": opcounters.get("delete", 0),
        "cache_bytes_in_use": wt.get("bytes currently in the cache", 0),
        "cache_max_bytes": wt.get("maximum bytes configured", 0),
        "cache_dirty_bytes": wt.get("tracked dirty bytes in the cache", 0),
        "pages_read_into_cache": wt.get("pages read into cache", 0),
    }


def format_table(metrics):
    """Create a rich table of metrics."""
    table = Table(title="MongoDB Metrics Dashboard")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Connections (current)", str(metrics["connections_current"]))
    table.add_row("Connections (available)", str(metrics["connections_available"]))
    table.add_row("Ops: Insert", f"{metrics['op_insert']:,}")
    table.add_row("Ops: Query", f"{metrics['op_query']:,}")
    table.add_row("Ops: Update", f"{metrics['op_update']:,}")
    table.add_row("Ops: Delete", f"{metrics['op_delete']:,}")
    cache_pct = 0
    if metrics["cache_max_bytes"] > 0:
        cache_pct = (metrics["cache_bytes_in_use"] / metrics["cache_max_bytes"]) * 100
    table.add_row("Cache Usage", f"{cache_pct:.1f}%")
    table.add_row("Cache Dirty Bytes", f"{metrics['cache_dirty_bytes']:,}")
    return table


def check_thresholds(metrics):
    """Check metric thresholds and alert."""
    alerts = []
    cache_pct = 0
    if metrics["cache_max_bytes"] > 0:
        cache_pct = (metrics["cache_bytes_in_use"] / metrics["cache_max_bytes"]) * 100
    if cache_pct > 80:
        alerts.append(f"[ALERT] Cache usage {cache_pct:.1f}% exceeds 80%!")
    if metrics["connections_current"] > metrics["connections_available"] * 0.8:
        alerts.append(f"[ALERT] Connections near limit: {metrics['connections_current']}/{metrics['connections_available']}")

    # Check replication lag if replica set
    try:
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=3000)
        repl_status = client.admin.command("replSetGetStatus")
        for m in repl_status.get("members", []):
            if m.get("stateStr") == "SECONDARY":
                lag = m.get("optimeDate", {}).get("$date", 0)
                if lag > 10000:
                    alerts.append(f"[ALERT] Replication lag on {m['name']}")
        client.close()
    except Exception:
        pass  # standalone, no repl

    return alerts


def main():
    banner("Lab 14.1: Monitoring Dashboard")
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("[OK] Connected. Starting monitoring loop (Ctrl+C to stop)...")

    try:
        for i in range(10):  # Run 10 iterations (every 3s = 30s total)
            metrics = get_metrics(client)
            console.clear()
            console.print(format_table(metrics))
            logging.info(json.dumps(metrics))

            alerts = check_thresholds(metrics)
            for alert in alerts:
                console.print(alert, style="bold red")
                logging.warning(alert)

            if i < 9:
                time.sleep(3)
    except KeyboardInterrupt:
        pass

    print("\nMetrics logged to: chapter-14/logs/metrics.log")
    client.close()
    banner("Lab 14.1 Complete")


if __name__ == "__main__":
    main()
