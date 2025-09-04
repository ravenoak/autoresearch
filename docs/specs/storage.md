# Storage

## Overview

The storage subsystem persists claims and enables hybrid retrieval across graph,
vector, and RDF backends. Simulations and targeted tests confirm schema
idempotency and RAM budget enforcement under concurrency [d1][s1][t4][t5][t6].

## Algorithms

- Implement core behaviors described above.

## Invariants

- Preserve documented state across operations.

## Proof Sketch

Core routines enforce invariants by validating inputs and state.

## Simulation Expectations

Unit tests cover nominal and edge cases for these routines.

## Traceability


- Modules
  - [src/autoresearch/storage.py][m1]
- Documents
  - [docs/algorithms/storage.md][d1]
- Scripts
  - [scripts/storage_eviction_sim.py][s1]
- Tests
  - [tests/behavior/features/storage_search_integration.feature][t1]
  - [tests/integration/test_search_storage.py][t2]
  - [tests/unit/test_storage_eviction.py][t3]
  - [tests/integration/test_storage_eviction.py][t4]
  - [tests/integration/test_storage_duckdb_fallback.py][t5]
  - [tests/targeted/test_storage_eviction.py][t6]

[m1]: ../../src/autoresearch/storage.py
[d1]: ../algorithms/storage.md
[s1]: ../../scripts/storage_eviction_sim.py
[t1]: ../../tests/behavior/features/storage_search_integration.feature
[t2]: ../../tests/integration/test_search_storage.py
[t3]: ../../tests/unit/test_storage_eviction.py
[t4]: ../../tests/integration/test_storage_eviction.py
[t5]: ../../tests/integration/test_storage_duckdb_fallback.py
[t6]: ../../tests/targeted/test_storage_eviction.py

## Troubleshooting

- **Missing tables after setup:** Run `initialize_storage()` to recreate the
  schema. In-memory databases start empty, so the helper ensures the required
  tables are present. Verify the DuckDB path is writable when using disk
  storage.
