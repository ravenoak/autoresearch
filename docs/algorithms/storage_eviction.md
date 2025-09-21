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

## Correctness

Let `B` be the budget and `δ` the safety margin. Denote usage by `U`. When
`_enforce_ram_budget` runs, it acquires a lock, reads `U₀`, and sets the
target `T = B(1 - δ)`. If `U₀ \leq B` the function returns. Otherwise each
iteration removes a node of size `sᵢ > 0` and updates
`Uᵢ₊₁ = Uᵢ - sᵢ`. The sequence `(Uᵢ)` is strictly decreasing and bounded
below by `0`, so after at most `⌈(U₀ - T) / s_min⌉` steps we obtain
`Uₖ \leq T`. Thus the invariant `U \leq B(1 - δ)` holds on exit.

**Concurrency.** Calls are serialized by a global lock. Independent threads
therefore observe a state satisfying the invariant and leave it intact.

**Boundary cases.**

- **Zero or negative budget:** If `B \leq 0` the function returns immediately.
- **Usage at or below budget:** When `U₀ \leq B` no nodes are evicted.
- **Empty graph:** The loop exits with no effect when there are no nodes to
  remove.
- **Missing metrics:** A 0 MB usage reading is treated as "unknown" and leaves
  the graph unchanged unless a deterministic override is configured. The
  deterministic fallback derived from `ram_budget_mb` only activates when
  metrics confirm `U > B`, keeping under-budget scenarios intact.

These arguments assume each node consumes at least `s_min > 0` MB, so the
termination bound above is finite.

## DuckDB Initialization

Use `initialize_storage()` when the DuckDB path is `:memory:`. In-memory
databases start empty on each run, so the helper recreates the `nodes`,
`edges`, `embeddings`, and `metadata` tables before eviction logic is
evaluated.

## Verification

Simulation tests [analysis-test]
and property checks [unit-test]
exercise access patterns and confirm deterministic eviction. The
simulation script [sim-script] models concurrent writers, dedicated
evictors, and edge cases such as zero, negative, exact, or under-budget
usage.

[analysis-test]: ../../tests/analysis/test_storage_eviction.py
[unit-test]: ../../tests/unit/test_storage_eviction.py
[sim-script]: ../../scripts/storage_eviction_sim.py
