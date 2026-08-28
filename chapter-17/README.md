# Chapter 17: AI-Native MongoDB -- Vector Search and RAG Foundations

## What You'll Learn

- What an embedding actually is: a vector representation of text where semantic similarity becomes geometric closeness, and why that's what makes semantic (as opposed to keyword) search possible
- The full shape of a RAG (Retrieval-Augmented Generation) pipeline: chunk documents, embed the chunks, retrieve the most relevant ones for a query via vector similarity, and feed them into an LLM prompt
- The difference between exact nearest-neighbor search and approximate nearest-neighbor (ANN) search, and why production vector databases use ANN at scale
- HNSW and IVF as two different ANN strategies, with a real, measurable recall-vs-speed trade-off between them -- not just as named algorithms

## Prerequisites

MongoDB running locally or on Atlas for Activity 1. Activity 2 needs nothing but NumPy -- it runs entirely offline against a synthetic dataset.

## Activity 1: Build a Simple RAG Pipeline [`lab_01_rag_pipeline.py`]

### Topics You Need First

**An embedding turns text into a vector such that similar meaning means small geometric distance.** Two sentences about the same topic, even with completely different words, should end up as vectors that are *close together* under a similarity measure like cosine similarity -- which is exactly what makes "search by meaning" possible instead of "search by exact keyword match."

**Cosine similarity, concretely.** It measures the angle between two vectors, ignoring their magnitude -- a value near 1 means "pointing in almost the same direction" (very similar), near 0 means "unrelated," and near -1 means "opposite." This activity's `cosine_similarity()` function computes it directly as a dot product, which only works correctly because the vectors are pre-normalized to unit length (`mock_embed` divides by the vector's norm before returning it).

**Mock embeddings vs. real embeddings.** This activity uses a deterministic *mock* embedding function (hashing the text to seed a random vector) so the whole pipeline runs offline with no API key and no cost -- but a mock embedding has no actual semantic meaning; two unrelated sentences that happen to hash similarly would incorrectly appear "similar." A real embedding model (VoyageAI, OpenAI, or similar, used in production and in Appendix A) is what makes retrieval quality meaningful.

**The RAG pipeline shape.** Chunk documents into passages &rarr; embed each chunk &rarr; store chunks + embeddings &rarr; for an incoming question, embed the question the same way &rarr; retrieve the chunks whose embeddings are most similar to the question's embedding &rarr; construct a prompt containing those chunks as context &rarr; send that prompt to an LLM. Every one of those steps is visible and inspectable in this activity's code.

### The Task

Several short documents about NoSQL/MongoDB topics are chunked and embedded (with the mock embedder). Given a sample question, the script embeds the question, finds the most similar chunks by brute-force cosine similarity, and constructs the context that would be sent to an LLM.

Before reading the retrieval step: predict, just from reading the seeded documents' titles and content, which document's chunk(s) *should* come back as most relevant for the sample question. Then check the actual retrieved chunks (and their similarity scores) against your prediction.

## Activity 2: Compare HNSW and IVF Vector Index Types [`lab_02_hnsw_vs_ivf.py`]

### Topics You Need First

**Why approximate search exists at all.** Brute-force search (compare the query against every single vector) gives perfect results but scales linearly with dataset size -- fine for thousands of vectors, prohibitively slow for billions. Approximate Nearest Neighbor (ANN) search trades a small, controllable amount of accuracy for a large reduction in how many vectors actually need to be compared per query.

**IVF (Inverted File Index): cluster first, then only search the closest clusters.** IVF groups all vectors into a small number of clusters (via something like k-means) ahead of time. At query time, it only searches the `nprobe` clusters whose centroid is closest to the query -- ignoring every vector in the other clusters entirely. Fewer clusters searched means faster but less accurate; more clusters searched trades speed back for accuracy.

**HNSW (Hierarchical Navigable Small World): a graph you traverse greedily.** Instead of clustering, HNSW connects each vector to a handful of its nearest neighbors, forming a navigable graph. A search starts from an entry point and greedily walks toward better-matching neighbors until it can't improve further. MongoDB Atlas's `$vectorSearch` uses a production-grade, multi-layer version of this. This activity's version is a simplified, single-layer relative built for intuition, not a benchmark of Atlas's actual implementation.

**Recall@k is the accuracy metric that matters here.** It's the fraction of the *true* top-k nearest neighbors (from exact brute-force search) that an approximate method actually found. 100% recall means the approximate method found exactly the same top-k as brute force; anything less means it missed some true neighbors in exchange for speed.

### The Task

The script builds a synthetic dataset of vectors, computes exact brute-force nearest-neighbor results as ground truth, then builds and queries both an IVF index and a simplified HNSW-like (NSW) index, reporting recall@k and the number of vectors actually compared per query for all three approaches.

Before running it: predict which of the two approximate methods (IVF or the NSW/HNSW-like index) will achieve higher recall in this experiment, and predict whether "vectors compared per query" or "wall-clock query time" is the more reliable metric to compare across the three methods in a pure-Python implementation like this one (the answer, and why, is spelled out in the script's own closing commentary -- compare your reasoning against it).

## Files in This Directory

| File | Purpose |
|---|---|
| `lab_01_rag_pipeline.py` | Activity 1 |
| `lab_02_hnsw_vs_ivf.py` | Activity 2 (no MongoDB connection needed) |

## Check Your Work

For Activity 1, the retrieved chunk(s) should come from the document whose actual subject matter (not just word overlap) matches the sample question -- if the mock embedder's hash-based "similarity" happens to retrieve an unrelated chunk instead, that's a useful, concrete illustration of exactly why mock embeddings aren't a substitute for real ones in an actual product.

For Activity 2, both IVF and the NSW/HNSW-like index should show recall well below 100% but well above 0% -- and the "vectors compared" column, not the millisecond column, should be what clearly shows both methods examining only a small fraction of the full dataset per query, which is the entire point of using an ANN index in the first place.
