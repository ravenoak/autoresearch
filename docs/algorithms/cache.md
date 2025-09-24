# Search Cache

The `SearchCache` stores search results keyed by query and backend in a TinyDB
file so repeated queries avoid duplicate work.

## Data layout
- Each row tracks `query`, `backend`, and a deep copy of `results` to avoid
  mutation. The upsert condition enforces uniqueness for the pair.

## Concurrency
- A `Lock` guards setup and teardown, ensuring the TinyDB handle is accessed by
  one thread at a time.

## Complexity
- `cache_results` performs an upsert which scans existing rows, costing
  `O(n)` for `n` cached entries.
- `get_cached_results` evaluates a TinyDB query with the same `O(n)` cost.

## Correctness
- Inserts and reads deep-copy data, so callers cannot mutate cached entries
  after retrieval.
- `clear` drops all tables, guaranteeing subsequent reads see an empty cache.

## Simulation
[`simulate_cache_eviction.py`](../../scripts/simulate_cache_eviction.py)
evicts the oldest entries until the TinyDB stays under a fixed size. The run
time grows linearly with the number of records, empirically confirming the
`O(n)` bounds above.

## Lookup flow

`Search.external_lookup` consults the cache before contacting any backend.
Cache hits still receive embeddings via `Search.add_embeddings`, ensuring the
storage hydration pipeline can reuse cached vectors and immediately merge the
results with DuckDB and ontology matches. Misses trigger the configured
backends, and the ranked documents are persisted so subsequent calls retrieve
hydrated results without another network round-trip.

## Fallback behaviour

The hybrid pipeline degrades gracefully when optional storage components are
unavailable. If the DuckDB VSS extension cannot load, the storage stage emits
only lexical and ontology results. When the RDF store is missing, ontology
queries are skipped but cached and BM25-ranked documents remain deterministic.
The cache therefore guarantees stable output even as optional extras come and
go.

## Document ingestion scope

Document caching mirrors the 0.1.0a1 decision to ship PDF and DOCX ingestion
behind the `parsers` extra. We debated marking binary formats unsupported, yet
that approach fragmented cached snippets across backends. Normalizing text via
`autoresearch.search.parsers` keeps cached entries consistent, while explicit
`ParserError` exceptions allow the cache to ignore corrupt or dependency-free
documents without polluting storage. Regression tests cover both success and
failure paths to preserve this contract.

## References
- [`cache.py`](../../src/autoresearch/cache.py)
- [spec](../specs/cache.md)
- [`test_cache.py`](../../tests/unit/test_cache.py)
- [`simulate_cache_eviction.py`][cache-sim]

[cache-sim]: ../../scripts/simulate_cache_eviction.py
