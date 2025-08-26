# Storage Eviction

Autoresearch bounds in-memory data by enforcing a RAM budget. The
`StorageManager` applies eviction policies when the budget is exceeded.

## RAM budget algorithm

Given a budget `B` megabytes and current usage `U`, the algorithm:

1. Measure current RAM.
2. If `U \leq B`, exit.
3. Compute target `T = B * (1 - safety_margin)` where the margin defaults
   to `10%`.
4. Select an eviction policy from configuration:
   - `lru` – remove least recently used nodes.
   - `score` – drop lowest confidence nodes.
   - `hybrid` – mix recency and score.
   - `adaptive` – choose `lru` or `score` based on access variance.
   - `priority` – evict by type tiers with confidence adjustments.
5. Remove nodes in batches until usage `\leq T`, updating metrics after
   each deletion.

The routine runs in `O(k)` time where `k` is the number of evicted nodes.
Removal touches only the NetworkX graph; DuckDB and RDF records persist.

## DuckDB Initialization

Use `initialize_storage()` when the DuckDB path is `:memory:`. In-memory
databases start empty on each run, so the helper recreates the `nodes`,
`edges`, `embeddings`, and `metadata` tables before eviction logic is
evaluated.

## Verification

Simulation tests [analysis-test]
and property checks [unit-test]
exercise access patterns and confirm deterministic eviction.

[analysis-test]: ../../tests/analysis/test_storage_eviction.py
[unit-test]: ../../tests/unit/test_storage_eviction.py
