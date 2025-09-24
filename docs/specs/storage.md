# Storage

## Overview

The storage subsystem persists claims and enables hybrid retrieval across
graph, vector, and RDF backends. Simulations and targeted tests confirm
schema idempotency, concurrency safety, and RAM budget enforcement
[d1][s1][s2][s3][s4][t4][t5][t6]. See the
[domain model](../domain_model.md) for storage context.

## Algorithms

- Implement core behaviors described above.

## State Transitions

Given storage state `(G, U, B)`:

- **Persist**
  `(G, U, B) ─persist(c)→ (G ∪ {c}, U + u(c), B)`
  and if `U + u(c) > B`, an eviction transition follows.

- **Evict**
 `(G, U, B) ─evict(E)→ (G \ E, U - u(E), B)`
  where `E` is a set of nodes such that `U - u(E) ≤ B(1 - δ)`.

## Invariants

State-transition invariants describe properties that hold for the storage state
`(G, U, B)` where `G` is the graph, `U` the RAM usage, `B` the budget, and `δ`
the safety margin.

1. **Setup**
   - Repeated `initialize_storage` calls leave `G` unchanged.
   - `StorageManager.setup` acquires `StorageState.lock` before calling
     `initialize_storage`, keeping DuckDB schema creation single-threaded even
     when multiple threads race to start storage [t125].
   - The eviction counter resets to zero.
2. **Persist**
   - Claim `c` does not exist in `G` prior to persistence.
   - After `persist_claim`, `c ∈ G` and `U' = U + u(c)`.
  - A re-entrant lock serializes writers so `G` reflects a linear history and
    LRU bookkeeping remains race-free.
   - If `U' > B`, subsequent eviction ensures `U'' ≤ B(1 - δ)`.
   - Persisted claims remain retrievable via `get_claim` across DuckDB sessions
     [t2].
3. **Evict**
   - Eviction chooses `E ⊆ G` per policy and yields
     `G' = G \ E` with `U' = U - u(E)`.
   - Each removed node increments the eviction counter [m2].
   - Repeating eviction on the same `E` leaves state unchanged.
4. **Budget guard**
   - When `B ≤ 0`, eviction is skipped and all nodes remain.
   - When `U ≤ B`, no eviction occurs and all nodes remain.
   - Deterministic node caps engage only when operators set
     `storage.deterministic_node_budget` or when metrics report `U > B`.
   - Stale policy caches no longer block eviction; if the LRU map is empty
     while `G` still contains nodes, `_enforce_ram_budget` selects fallback
     candidates directly from `G` before checking the RAM margin and the
     deterministic cap.
5. **Teardown**
   - `teardown` clears `G` and releases resources.

## Edge Cases

- A budget of zero or a negative value disables eviction.
- Enforcing the budget on an empty graph leaves state unchanged.
- A 0 MB usage reading is treated as "unknown" and leaves the graph unchanged
  unless a deterministic override is configured.
- `storage.deterministic_node_budget` optionally enforces a hard node cap even
  when usage metrics are unavailable.

## Configuration Notes

- `storage.deterministic_node_budget` limits the in-memory graph to a fixed
  size. Absent this override, deterministic caps derive from `ram_budget_mb`
  only when `U > B`, maintaining the "no eviction when `U ≤ B`" invariant.

## Complexity

For a graph with `n` nodes and an eviction set `E` of size `k`:

- LRU eviction costs `O(k log n)` due to priority queue operations.
- Budget enforcement scans at most `n` nodes, yielding `O(n)` time and
  `O(n)` space.

## Proof Sketch

- `initialize_storage` uses `CREATE TABLE IF NOT EXISTS`, so repeated runs
  yield identical table listings, demonstrated in
  `schema_idempotency_sim.py` [s2]. Schema version detection relies on
  `fetchall` so connections without `fetchone` remain supported.
- **Concurrency safety.** A single re-entrant lock guards state, so any
  interleaving `t₁, t₂, …` reduces to a serial order. Graph updates, LRU
  counters, and even `StorageManager.setup` re-acquire the lock before
  `initialize_storage`, eliminating the DuckDB schema race that previously
  crashed under load. The resulting sequence `σ₀ ─t₁→ σ₁ ─t₂→ σ₂` preserves
  linearizability, `storage_concurrency_sim.py` [s4] confirms mixed states
  cannot appear, and `test_setup_thread_safe` guards against regressions [t125].
- **Eviction termination.** Let `U_i` be usage after step `i` and `E_i` the
  evicted set with `u(E_i) > 0`. Then `U_{i+1} = U_i - u(E_i)` and the
  decreasing sequence `{U_i}` is bounded below by `0`, so some `U_k` satisfies
  `U_k ≤ B(1 - δ)`.
- **RAM-budget enforcement.** `_enforce_ram_budget` applies `evict` while
  `U > B(1 - δ)`, and simulations [s1][s3] validate this bound.
- **Disabled budgets.** When `B ≤ 0` the helper performs no eviction,
  demonstrated in `storage_eviction_sim.py` [s1].

These arguments rely on the formal proofs and simulations in
[docs/algorithms/storage.md][d1].

## Simulation Expectations

Unit tests and simulations cover nominal and edge cases for these routines,
including `storage_eviction_sim.py` [s1], `schema_idempotency_sim.py` [s2],
`ram_budget_enforcement_sim.py` [s3], and `storage_concurrency_sim.py` [s4].

## Simulation Benchmarks

Integration tests exercise these simulations to validate concurrency safety and
RAM-budget enforcement.

- `test_concurrency_benchmark` spawns two writer threads and leaves zero nodes
  [t8].
- `test_ram_budget_benchmark` persists five items sequentially and evicts down
  to zero nodes [t8].

## Example Results

`schema_idempotency_sim.py` reports `schema stable across 3 runs` [s2r].
`storage_eviction_sim.py` with two threads and five items leaves zero nodes and
achieves roughly `0.3 nodes/s` throughput [s1r].
`storage_eviction_sim.py` with a zero budget retains all nodes [s1].
`storage_concurrency_sim.py` with six setup threads and four items prints
`setup calls: 1`, `setup failures: 0`, and `unique contexts: 1`, showing
single initialization even under contention [s4m].
`test_ram_budget_benchmark` measures mean eviction latency of about `3.2 s`
and `0.31 OPS` [t5r].

## Benchmark Output

`test_ram_budget_benchmark` measures eviction latency; results appear in
[tests/integration/test_storage_duckdb_fallback.py][t5] and in the
[DuckDB fallback benchmark][b1].

## Concurrency Assumptions

- A process-wide re-entrant lock serializes graph mutations.
- `_enforce_ram_budget` holds this lock, preventing eviction races.
- Concurrent writers stay within budget in `storage_concurrency_sim.py` [s4].
- `StorageManager.setup` serializes DuckDB initialization, avoiding
  segmentation faults seen when concurrent threads touched
  `initialize_storage` [t125].

## Traceability

- Modules
  - [src/autoresearch/storage.py][m1]
- Metrics
  - [src/autoresearch/storage.py#L729][m2]
- Documents
  - [docs/algorithms/storage.md][d1]
- Scripts
  - [scripts/storage_eviction_sim.py][s1]
  - [scripts/schema_idempotency_sim.py][s2]
  - [scripts/ram_budget_enforcement_sim.py][s3]
  - [scripts/storage_concurrency_sim.py][s4]
- Benchmarks
  - [docs/algorithms/storage.md#duckdb-fallback-benchmark][b1]
- Tests
  - [tests/behavior/features/storage_search_integration.feature][t1]
  - [tests/integration/test_search_storage.py][t2]
  - [tests/unit/test_storage_eviction.py][t3]
  - [tests/integration/test_storage_eviction.py][t4]
  - [tests/integration/test_storage_duckdb_fallback.py][t5]
  - [tests/targeted/test_storage_eviction.py][t6]
  - [tests/unit/test_storage_eviction_sim.py][t7]
  - [tests/unit/test_storage_manager_concurrency.py][t125]
  - [tests/integration/storage/test_simulation_benchmarks.py][t8]
  - [tests/integration/test_rdf_persistence.py][t9]

[m1]: ../../src/autoresearch/storage.py
[m2]: ../../src/autoresearch/storage.py#L729
[d1]: ../algorithms/storage.md
[s1]: ../../scripts/storage_eviction_sim.py
[s1r]: ../../scripts/storage_eviction_sim.py
[s2]: ../../scripts/schema_idempotency_sim.py
[s2r]: ../../scripts/schema_idempotency_sim.py
[s3]: ../../scripts/ram_budget_enforcement_sim.py
[s4]: ../../scripts/storage_concurrency_sim.py
[s4m]: ../algorithms/storage.md#setup-concurrency-metrics
[b1]: ../algorithms/storage.md#duckdb-fallback-benchmark
[t1]: ../../tests/behavior/features/storage_search_integration.feature
[t2]: ../../tests/integration/test_search_storage.py
[t3]: ../../tests/unit/test_storage_eviction.py
[t4]: ../../tests/integration/test_storage_eviction.py
[t5]: ../../tests/integration/test_storage_duckdb_fallback.py
[t5r]: ../../tests/integration/test_storage_duckdb_fallback.py
[t6]: ../../tests/targeted/test_storage_eviction.py
[t7]: ../../tests/unit/test_storage_eviction_sim.py
[t125]: ../../tests/unit/test_storage_manager_concurrency.py
[t8]: ../../tests/integration/storage/test_simulation_benchmarks.py
[t9]: ../../tests/integration/test_rdf_persistence.py

## Troubleshooting

- **Missing tables after setup:** Run `initialize_storage()` to recreate the
  schema. In-memory databases start empty, so the helper ensures the required
  tables are present. Verify the DuckDB path is writable when using disk
  storage.
