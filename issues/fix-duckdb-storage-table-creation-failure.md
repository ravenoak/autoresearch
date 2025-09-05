# Fix DuckDB storage table creation failure

## Context
`task verify` fails in `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_create_tables`
with `StorageError: Failed to create tables`. The DuckDB storage backend must initialize
its tables for unit tests and the alpha release.

## Dependencies
None.

## Acceptance Criteria
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_create_tables` passes.
- `task verify` completes the DuckDB storage backend unit tests without errors.
- The changelog records the fix.

## Status
Open
