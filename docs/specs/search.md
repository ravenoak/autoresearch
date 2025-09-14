# Search Module Specification

## Overview

The search package (`src/autoresearch/search/`) retrieves information from
local files, storage backends, and vector indexes. It supports keyword, vector,
and hybrid queries and exposes a CLI entry point.

## Algorithms

### Keyword

- Uses a BM25-style ranking over tokenized documents.
- Returns top `k` documents sorted by term frequency–inverse document
  frequency (TF-IDF) scores.

### Vector

- Embeds documents and queries into a shared space.
- Performs k-nearest neighbor search over the vector index using cosine
  similarity.

### Hybrid

- Computes keyword and vector scores separately.
- Normalizes semantic and DuckDB similarities before averaging so hybrid and
  semantic rankings share a unified scale.
- Combines results with a weighted sum of keyword, vector, and source
  credibility weights.
- Resolves ties by deterministic document identifier.

## Invariants

- Results are ordered by descending final score and are stable for repeated
  queries, yielding consistent ordering across hybrid and semantic modes.
- Indexing is idempotent: re-ingesting an existing document updates the record
  without creating duplicates.
- Search does not mutate stored documents outside explicit persist or update
  calls.

## Proof Sketch

- **Ordering:** Each algorithm returns a scored list, and the hybrid combiner
  sorts the merged list before returning. Deterministic tie-breaking yields
  stable output.
- **Idempotent indexing:** Storage operations keyed by unique identifiers
  overwrite existing entries. Refreshing the vector index ensures updated
  embeddings are used without duplicating nodes.
- **Safety:** Read-only search paths call storage through read operations, so
  queries cannot modify claims.

## Simulation Expectations

- `hybrid_search.feature` shows keyword and vector results appear together.
- `local_sources.feature` verifies keyword search finds local files.
- `vector_search_performance.feature` measures embedding search latency.
- `test_search_reflects_updated_claim` demonstrates index updates are
  visible.
- `test_search_results_stable` guards against result ordering regressions.
