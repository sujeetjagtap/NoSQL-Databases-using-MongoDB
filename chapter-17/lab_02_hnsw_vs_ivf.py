"""Lab 17.2 - Compare HNSW and IVF Vector Index Types

MongoDB Atlas Vector Search uses HNSW (Hierarchical Navigable Small World)
graphs under the hood for its $vectorSearch stage. IVF (Inverted File
Index, cluster-based) is the other major approximate nearest neighbor
(ANN) family you will see in other vector databases (e.g. FAISS, some
Postgres pgvector configurations). This lab builds simplified versions of
both from scratch with NumPy so you can SEE the recall/speed trade-off
they make relative to exact brute-force search, on a synthetic dataset,
entirely offline (no MongoDB or Atlas connection required for this lab).

Honesty note: these are simplified, single-machine, educational
implementations meant to build intuition about the trade-offs -- NOT
production-grade or a benchmark of Atlas's actual (multi-layer,
highly-optimized) HNSW implementation. For real workloads, use Atlas
Vector Search ($vectorSearch) directly, or a dedicated library like
`hnswlib` or `faiss` if you need ANN search outside MongoDB.
"""

import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from config.connection import banner
from rich.table import Table
from rich.console import Console

console = Console()

random.seed(42)
np.random.seed(42)

N_VECTORS = 3000
DIM = 64
N_QUERIES = 20
K = 10


def make_dataset():
    """Synthetic unit-normalized vectors, standing in for document embeddings."""
    data = np.random.normal(size=(N_VECTORS, DIM)).astype(np.float32)
    data /= np.linalg.norm(data, axis=1, keepdims=True)
    queries = np.random.normal(size=(N_QUERIES, DIM)).astype(np.float32)
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)
    return data, queries


# --- Baseline: exact brute-force search ---
def brute_force_search(data, query, k):
    scores = data @ query  # cosine similarity (vectors are unit-normalized)
    top_k = np.argsort(-scores)[:k]
    return top_k


# --- IVF: cluster-then-search ---
class IVFIndex:
    """Partitions vectors into `nlist` clusters (via a small k-means run).
    A query only scans the `nprobe` clusters whose centroid is closest to
    it, trading a chance of missing a true neighbor in an unscanned
    cluster for a large reduction in vectors compared per query."""

    def __init__(self, nlist=20):
        self.nlist = nlist

    def build(self, data):
        start = time.perf_counter()
        n = data.shape[0]
        rng = np.random.default_rng(42)
        centroid_idx = rng.choice(n, size=self.nlist, replace=False)
        centroids = data[centroid_idx].copy()

        # A handful of Lloyd's-algorithm iterations is enough for this demo.
        for _ in range(8):
            sims = data @ centroids.T
            assignments = np.argmax(sims, axis=1)
            for c in range(self.nlist):
                members = data[assignments == c]
                if len(members) > 0:
                    centroids[c] = members.mean(axis=0)
                    centroids[c] /= np.linalg.norm(centroids[c]) + 1e-9

        self.centroids = centroids
        self.assignments = assignments
        self.data = data
        self.buckets = {c: np.where(assignments == c)[0] for c in range(self.nlist)}
        self.build_time = time.perf_counter() - start

    def search(self, query, k, nprobe=3):
        centroid_scores = self.centroids @ query
        probe_clusters = np.argsort(-centroid_scores)[:nprobe]
        candidate_idx = np.concatenate([self.buckets[c] for c in probe_clusters]) \
            if len(probe_clusters) else np.array([], dtype=int)
        if len(candidate_idx) == 0:
            return np.array([], dtype=int), 0
        candidate_scores = self.data[candidate_idx] @ query
        top_local = np.argsort(-candidate_scores)[:k]
        return candidate_idx[top_local], len(candidate_idx)


# --- Simplified NSW (a single-layer relative of HNSW) ---
class SimpleNSWIndex:
    """A simplified, single-layer Navigable Small World graph. Real HNSW
    adds multiple layers (a coarse "highway" layer for long jumps, finer
    layers for local search) on top of this same idea; this single-layer
    version is enough to demonstrate the core trade-off: greedy graph
    search visits far fewer vectors than brute force, at some recall cost."""

    def __init__(self, m=16, ef_construction=150):
        self.m = m                          # neighbors per node
        self.ef_construction = ef_construction

    def build(self, data):
        start = time.perf_counter()
        n = data.shape[0]
        self.data = data
        self.graph = {i: set() for i in range(n)}

        for i in range(n):
            if i == 0:
                continue
            # Candidate pool: a random sample of already-inserted nodes,
            # standing in for a real graph-guided search during insertion.
            pool_size = min(self.ef_construction, i)
            candidates = np.random.default_rng(i).choice(i, size=pool_size, replace=False)
            sims = data[candidates] @ data[i]
            nearest = candidates[np.argsort(-sims)[: self.m]]
            for j in nearest:
                self.graph[i].add(int(j))
                self.graph[int(j)].add(i)

        self.build_time = time.perf_counter() - start

    def search(self, query, k, ef_search=100, n_entry_points=5):
        """Standard NSW greedy search: maintain a frontier of candidates to
        expand and a bounded result set of the `ef_search` best candidates
        seen so far, expanding through graph edges until no candidate could
        possibly improve the result set."""
        import heapq

        n = self.data.shape[0]
        rng = np.random.default_rng(0)
        entry_points = rng.choice(n, size=min(n_entry_points, n), replace=False)

        visited = set()
        candidates = []   # max-heap via negated score: (-score, node)
        results = []      # min-heap of (score, node), bounded to ef_search

        for ep in entry_points:
            ep = int(ep)
            if ep in visited:
                continue
            visited.add(ep)
            score = float(self.data[ep] @ query)
            heapq.heappush(candidates, (-score, ep))
            heapq.heappush(results, (score, ep))

        while candidates:
            neg_score, node = heapq.heappop(candidates)
            score = -neg_score
            worst_result_score = results[0][0] if len(results) >= ef_search else float("-inf")
            if score < worst_result_score:
                break  # nothing left in the frontier can improve the result set

            for neighbor in self.graph[node]:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                n_score = float(self.data[neighbor] @ query)
                worst_result_score = results[0][0] if len(results) >= ef_search else float("-inf")
                if n_score > worst_result_score or len(results) < ef_search:
                    heapq.heappush(candidates, (-n_score, neighbor))
                    heapq.heappush(results, (n_score, neighbor))
                    if len(results) > ef_search:
                        heapq.heappop(results)

        results.sort(key=lambda x: -x[0])
        return np.array([node for _, node in results[:k]]), len(visited)


def recall_at_k(predicted: np.ndarray, ground_truth: np.ndarray) -> float:
    if len(predicted) == 0:
        return 0.0
    return len(set(predicted.tolist()) & set(ground_truth.tolist())) / len(ground_truth)


def main():
    banner("Lab 17.2: Compare HNSW and IVF Vector Index Types")

    print(f"=== Step 1: Generate synthetic dataset ({N_VECTORS} vectors, dim={DIM}) ===")
    data, queries = make_dataset()
    print(f"  [OK] Dataset ready. {N_QUERIES} queries, k={K}.")

    print("\n=== Step 2: Compute exact (brute-force) ground truth ===")
    start = time.perf_counter()
    ground_truths = [brute_force_search(data, q, K) for q in queries]
    brute_time = (time.perf_counter() - start) / N_QUERIES
    print(f"  [OK] Ground truth computed. Avg query time: {brute_time*1000:.3f} ms")

    print("\n=== Step 3: Build and query IVF index ===")
    ivf = IVFIndex(nlist=20)
    ivf.build(data)
    start = time.perf_counter()
    ivf_search_results = [ivf.search(q, K, nprobe=3) for q in queries]
    ivf_time = (time.perf_counter() - start) / N_QUERIES
    ivf_results = [r for r, _ in ivf_search_results]
    ivf_compared = np.mean([n for _, n in ivf_search_results])
    ivf_recall = np.mean([recall_at_k(r, gt) for r, gt in zip(ivf_results, ground_truths)])
    print(f"  [OK] IVF built in {ivf.build_time*1000:.1f} ms. "
          f"Avg vectors compared/query: {ivf_compared:.0f}/{N_VECTORS}. "
          f"Recall@{K}: {ivf_recall:.2%}")

    print("\n=== Step 4: Build and query simplified NSW (HNSW-like) index ===")
    nsw = SimpleNSWIndex(m=16, ef_construction=150)
    nsw.build(data)
    start = time.perf_counter()
    nsw_search_results = [nsw.search(q, K, ef_search=100) for q in queries]
    nsw_time = (time.perf_counter() - start) / N_QUERIES
    nsw_results = [r for r, _ in nsw_search_results]
    nsw_compared = np.mean([n for _, n in nsw_search_results])
    nsw_recall = np.mean([recall_at_k(r, gt) for r, gt in zip(nsw_results, ground_truths)])
    print(f"  [OK] NSW built in {nsw.build_time*1000:.1f} ms. "
          f"Avg vectors compared/query: {nsw_compared:.0f}/{N_VECTORS}. "
          f"Recall@{K}: {nsw_recall:.2%}")

    print("\n=== Results ===")
    table = Table(title=f"ANN Index Comparison (N={N_VECTORS}, dim={DIM}, k={K})")
    table.add_column("Index Type", style="cyan")
    table.add_column("Build Time (ms)", justify="right")
    table.add_column("Vectors Compared/Query", justify="right")
    table.add_column("Avg Query Time (ms)", justify="right")
    table.add_column(f"Recall@{K}", justify="right")
    table.add_row("Brute-force (exact)", "0.0", f"{N_VECTORS} (100%)",
                  f"{brute_time*1000:.3f}", "100.00%")
    table.add_row("IVF (nlist=20, nprobe=3)", f"{ivf.build_time*1000:.1f}",
                  f"{ivf_compared:.0f} ({ivf_compared/N_VECTORS:.0%})",
                  f"{ivf_time*1000:.3f}", f"{ivf_recall:.2%}")
    table.add_row("Simplified NSW (HNSW-like)", f"{nsw.build_time*1000:.1f}",
                  f"{nsw_compared:.0f} ({nsw_compared/N_VECTORS:.0%})",
                  f"{nsw_time*1000:.3f}", f"{nsw_recall:.2%}")
    console.print(table)

    print("\n  Key takeaway: 'vectors compared per query' is the metric that actually")
    print("  explains why ANN indexes exist -- both IVF and NSW touch a small fraction")
    print("  of the dataset per query instead of all of it, and that fraction shrinks")
    print("  further as the dataset grows, which is where the real speed win shows up")
    print("  at production scale (millions of vectors). At this lab's small N and in")
    print("  pure Python, wall-clock time is dominated by per-node Python/heap overhead")
    print("  rather than raw comparisons, so don't read the millisecond column as a")
    print("  preview of Atlas's actual (compiled, multi-layer HNSW) performance --")
    print("  read the 'vectors compared' column instead, and treat the ms column as")
    print("  specific to this pure-Python educational implementation.")
    print("  IVF here trades more recall for speed (fewer clusters scanned); NSW trades")
    print("  more comparisons for recall. Try changing nprobe and ef_search yourself")
    print("  and watch recall and vectors-compared move together.")

    banner("Lab 17.2 Complete")


if __name__ == "__main__":
    main()
