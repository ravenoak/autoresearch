# Storage Initialization

## Overview

Storage initialization prepares DuckDB and its vector extension so that
callers can persist and query graph data. This spec covers extension
downloads and table creation routines.

## Algorithms

- **Extension download:** `scripts/download_duckdb_extensions.py` downloads
  required extensions. It retries network failures, then loads a cached copy
  recorded in `.env.offline`. If no copy exists, it creates an empty stub so
  subsequent runs can still proceed.
- **Table creation:** `initialize_storage` opens a DuckDB connection and
  invokes `_create_tables` on the backend. The helper issues `CREATE TABLE IF
  NOT EXISTS` for `nodes`, `edges`, `embeddings`, and `metadata` so that the
  schema is present on first use.

## Invariants

- After running the extension algorithm, an extension file exists at the
  target path even when downloads fail.
- After calling `initialize_storage`, all required tables exist and repeated
  calls leave the schema unchanged.

## Proof Sketch

- The extension routine ensures file existence by checking the cache after
  network retries and writing an empty stub when nothing is available. Thus,
  callers always encounter a file, satisfying the first invariant.
- `_create_tables` uses `CREATE TABLE IF NOT EXISTS` for each required table.
  The command is idempotent, so every invocation yields the same table set,
  proving the second invariant.

## Simulation Expectations

- Simulate network failures with [`download_duckdb_extensions` tests][download].
  `test_download_extension_network_fallback` observes a stub file when
  downloads fail.
- Verify table creation with `tests/unit/test_storage_persistence.py`.
  The `test_initialize_creates_tables_and_teardown_removes_file` test confirms
  the tables exist and the DB file is removed on teardown.

## Traceability

- Extension handling: [scripts/download_duckdb_extensions.py][dde]
- Storage setup: [src/autoresearch/storage.py][storage]
- Backend logic: [src/autoresearch/storage_backends.py][backend]
- Tests: [tests/unit/test_storage_persistence.py][persistence],
  [tests/unit/test_duckdb_storage_backend.py][backend-test]

[dde]: ../../scripts/download_duckdb_extensions.py
[storage]: ../../src/autoresearch/storage.py
[backend]: ../../src/autoresearch/storage_backends.py
[persistence]: ../../tests/unit/test_storage_persistence.py
[backend-test]: ../../tests/unit/test_duckdb_storage_backend.py
[download]: ../../tests/unit/test_download_duckdb_extensions.py
