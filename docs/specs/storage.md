# Storage

## Overview

The storage subsystem persists claims and enables hybrid retrieval across
graph, vector, and RDF backends. Simulations and targeted tests confirm
schema idempotency, concurrency safety, and RAM budget enforcement
[d1][s1][s2][s3][s4][t4][t5][t6].

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
2. **Persist**
   - After `persist_claim` and budget enforcement, `U ≤ B` unless
     `B ≤ 0`.
3. **Evict**
   - `_enforce_ram_budget` removes nodes until `U ≤ B(1 - δ)`.
4. **Under budget**
   - When `U ≤ B`, no eviction occurs and all nodes remain.
5. **Teardown**
   - `teardown` clears `G` and releases resources.

## Proof Sketch

- `initialize_storage` uses `CREATE TABLE IF NOT EXISTS`, so repeated runs yield
  identical table listings, demonstrated in `schema_idempotency_sim.py` [s2].
- **Concurrency safety.** Each transition acquires a re-entrant lock, yielding
  sequences like `σ₀ ─t₁→ σ₁ ─t₂→ σ₂`. Mixed states cannot appear, and
  `storage_concurrency_sim.py` [s4] exercises this ordering.
- **RAM-budget enforcement.** `_enforce_ram_budget` applies `evict` while
  `U > B(1 - δ)`. Let `U_i` be usage after step `i`; each step removes some
  `u_i > 0`, so `U_{i+1} = U_i - u_i`. The strictly decreasing sequence has a
  lower bound, yielding `U_k ≤ B(1 - δ)` for some `k`. Simulations [s1][s3]
  validate this bound.

These arguments rely on the formal proofs and simulations in
[docs/algorithms/storage.md][d1].

## Simulation Expectations

Unit tests and simulations cover nominal and edge cases for these routines,
including `storage_eviction_sim.py` [s1], `schema_idempotency_sim.py` [s2],
`ram_budget_enforcement_sim.py` [s3], and `storage_concurrency_sim.py` [s4].

## Benchmark Output

`test_ram_budget_benchmark` measures eviction latency; results appear in the
[DuckDB fallback benchmark][b1].

## Concurrency Assumptions

- A process-wide re-entrant lock serializes graph mutations.
- `_enforce_ram_budget` holds this lock, preventing eviction races.
- Concurrent writers stay within budget in `storage_concurrency_sim.py` [s4].

## Traceability

- Modules
  - [src/autoresearch/storage.py][m1]
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

[m1]: ../../src/autoresearch/storage.py
[d1]: ../algorithms/storage.md
[s1]: ../../scripts/storage_eviction_sim.py
[s2]: ../../scripts/schema_idempotency_sim.py
[s3]: ../../scripts/ram_budget_enforcement_sim.py
[s4]: ../../scripts/storage_concurrency_sim.py
[b1]: ../algorithms/storage.md#duckdb-fallback-benchmark
[t1]: ../../tests/behavior/features/storage_search_integration.feature
[t2]: ../../tests/integration/test_search_storage.py
[t3]: ../../tests/unit/test_storage_eviction.py
[t4]: ../../tests/integration/test_storage_eviction.py
[t5]: ../../tests/integration/test_storage_duckdb_fallback.py
[t6]: ../../tests/targeted/test_storage_eviction.py
[t7]: ../../tests/unit/test_storage_eviction_sim.py

## Troubleshooting

- **Missing tables after setup:** Run `initialize_storage()` to recreate the
  schema. In-memory databases start empty, so the helper ensures the required
  tables are present. Verify the DuckDB path is writable when using disk
  storage.
