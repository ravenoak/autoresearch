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

## References
- [`cache.py`](../../src/autoresearch/cache.py)
- [spec](../specs/cache.md)
- [`test_cache.py`](../../tests/unit/test_cache.py)
- [`simulate_cache_eviction.py`][cache-sim]

[cache-sim]: ../../scripts/simulate_cache_eviction.py
