# Storage Utilities

## Overview
Helpers for storage routines that ensure schema metadata exists.

## Algorithms
- `initialize_schema_version_without_fetchone` uses `fetchall` to read
  metadata and inserts version `1` if missing.

## Invariants
- Metadata table contains a single `schema_version` row.

## Proof Sketch
The function inserts only when no row is returned, preserving uniqueness.

## Simulation Expectations
Integration tests simulate a DuckDB connection without `fetchone`.

## Traceability

- Modules
  - [src/autoresearch/storage_utils.py][m1]
- Tests
  - [tests/integration/test_storage_schema.py][t1]

[m1]: ../../src/autoresearch/storage_utils.py
[t1]: ../../tests/integration/test_storage_schema.py
