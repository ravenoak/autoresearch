# Search Module Specification

## Overview

The search package (`src/autoresearch/search/`) retrieves information from
local files, storage backends, and vector indexes. It supports keyword, vector,
and hybrid queries and exposes a CLI entry point. See the
[domain model](../domain_model.md) for search relationships.

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
- Computes a convex combination of normalized BM25, semantic, and credibility
  scores:

  \[
  s = \text{normalize}(b w_b + v w_v + c w_c)
  \]

  where ``b``, ``v``, and ``c`` are the min–max normalized component scores
  and the weights ``w_b + w_v + w_c = 1``. If all configured weights are zero,
  ranking falls back to equal weighting across enabled components.
- Resolves ties by deterministic document identifier.

## Invariants

- Results are ordered by descending final score and are stable for repeated
  queries, yielding consistent ordering across hybrid and semantic modes.
- Indexing is idempotent: re-ingesting an existing document updates the record
  without creating duplicates.
- Search does not mutate stored documents outside explicit persist or update
  calls.
- When `return_handles=True`, `Search.external_lookup` returns an
  `ExternalLookupResult` containing the ranked documents, a backend map,
  and handles to the shared cache and storage manager.

## Cache Contract

- `autoresearch.cache.canonicalize_query_text` collapses whitespace and
  lowercases queries before fingerprinting so cache keys ignore superficial
  formatting differences.
- `autoresearch.cache.hash_cache_dimensions` hashes the canonical query,
  namespace, embedding signature, hybrid toggles, and storage hints into a
  deterministic fingerprint shared by all cache consumers.
- `autoresearch.cache.build_cache_key` combines the fingerprint with backend
  and embedding state metadata, emitting a `CacheKey.primary` string prefixed
  with `v3:` while surfacing the previous `v2:` hash in
  `CacheKey.aliases` and the legacy pipe-delimited key in `CacheKey.legacy`.
- `Search.external_lookup` and `Search.embedding_lookup` persist payloads under
  the primary hash, all aliases, and the legacy key, upgrading any legacy or v2
  hits to the new fingerprint so sequential requests survive hybrid toggles,
  storage hint changes, and historical cache snapshots.
- Hybrid enrichment pushes canonical and raw canonical query text to the
  diagnostics context so embedding augmentation remains deterministic for every
  query variant that resolves to the same canonical form.

## Public API

- `Search.external_lookup(query, max_results=5, *, return_handles=False)` is a
  hybridmethod. It can be invoked on an instance or on the class, which will
  delegate to the shared singleton. Monkeypatched doubles must accept the
  implicit instance argument to keep parity with production
  behaviour.
- `Search.embedding_lookup(query_embedding, max_results=5)` and
  `Search.add_embeddings(documents, query_embedding=None)` share the same
  hybridmethod behaviour. Tests should wrap stubs with the
  `hybridmethod` descriptor (or equivalent helper) so that both access paths
  continue to work.

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

## Traceability


- Modules
  - [src/autoresearch/search/][m1]
- Tests
  - [tests/behavior/features/hybrid_search.feature][t100]
  - [tests/behavior/features/local_sources.feature][t101]
  - [tests/behavior/features/search_cli.feature][t102]
  - [tests/behavior/features/storage_search_integration.feature][t103]
  - [tests/behavior/features/vector_search_performance.feature][t104]
  - [tests/integration/test_config_hot_reload_components.py][t41]
  - [tests/integration/test_search_regression.py][t105]
  - [tests/integration/test_search_storage.py][t106]
  - [tests/unit/legacy/test_search.py][t127]
  - [tests/unit/legacy/test_search.py][t128]
  - [tests/unit/legacy/test_search_parsers.py][t133]
  - [tests/unit/legacy/test_relevance_ranking.py][t134]
  - [tests/unit/legacy/test_relevance_ranking.py][t135]
  - [tests/unit/legacy/test_property_bm25_normalization.py][t136]
  - [tests/unit/legacy/test_ranking_idempotence.py][t138]
  - [tests/unit/legacy/test_property_search_ranking.py][t140]
  - [tests/unit/legacy/test_search.py][t141]
  - [tests/unit/legacy/test_search_parsers.py][t129]
  - [tests/unit/legacy/test_search_parsers.py][t130]
  - [tests/unit/legacy/test_search_parsers.py][t131]
  - [tests/unit/legacy/test_search_parsers.py][t132]
  - [tests/unit/legacy/test_search_parsers.py][t142]
  - [tests/unit/legacy/test_search_parsers.py][t143]
  - [tests/unit/legacy/test_search_parsers.py][t144]
  - [tests/unit/legacy/test_search_parsers.py][t145]

[m1]: ../../src/autoresearch/search/

[t100]: ../../tests/behavior/features/hybrid_search.feature
[t101]: ../../tests/behavior/features/local_sources.feature
[t102]: ../../tests/behavior/features/search_cli.feature
[t103]: ../../tests/behavior/features/storage_search_integration.feature
[t104]: ../../tests/behavior/features/vector_search_performance.feature
[t41]: ../../tests/integration/test_config_hot_reload_components.py
[t105]: ../../tests/integration/test_search_regression.py
[t106]: ../../tests/integration/test_search_storage.py
[t127]: ../../tests/unit/legacy/test_search.py
[t128]: ../../tests/unit/legacy/test_search.py
[t133]: ../../tests/unit/legacy/test_search_parsers.py
[t134]: ../../tests/unit/legacy/test_relevance_ranking.py
[t135]: ../../tests/unit/legacy/test_relevance_ranking.py
[t136]: ../../tests/unit/legacy/test_property_bm25_normalization.py
[t138]: ../../tests/unit/legacy/test_ranking_idempotence.py
[t140]: ../../tests/unit/legacy/test_property_search_ranking.py
[t141]: ../../tests/unit/legacy/test_search.py
[t129]: ../../tests/unit/legacy/test_search_parsers.py
[t130]: ../../tests/unit/legacy/test_search_parsers.py
[t131]: ../../tests/unit/legacy/test_search_parsers.py
[t132]: ../../tests/unit/legacy/test_search_parsers.py
[t142]: ../../tests/unit/legacy/test_search_parsers.py
[t143]: ../../tests/unit/legacy/test_search_parsers.py
[t144]: ../../tests/unit/legacy/test_search_parsers.py
[t145]: ../../tests/unit/legacy/test_search_parsers.py
