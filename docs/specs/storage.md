# Storage

## Overview

The storage subsystem persists claims and enables hybrid retrieval across
graph, vector, and RDF backends. Simulations and targeted tests confirm
schema idempotency, concurrency safety, and RAM budget enforcement
[d1][s1][s2][s3][s4][t4][t5][t6].

## Algorithms

- Implement core behaviors described above.

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
- `_enforce_ram_budget` acquires the lock and decreases usage while
  `U > B(1 - δ)`. Each step evicts at least one node, forming a decreasing
  sequence bounded below, so the loop halts within the budget. Sequential and
  concurrent simulations validate the bound [s3][s4].
- When `U ≤ B`, the loop does not run, preserving all nodes.

These arguments rely on the formal proofs and simulations in
[docs/algorithms/storage.md][d1].

## Simulation Expectations

Unit tests and simulations cover nominal and edge cases for these routines,
including `storage_eviction_sim.py`, `schema_idempotency_sim.py`,
`ram_budget_enforcement_sim.py`, and `storage_concurrency_sim.py`.

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
