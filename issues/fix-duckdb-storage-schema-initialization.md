# Fix DuckDB storage schema initialization

## Context
`task verify` fails in `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_initialize_schema_version` because the mock insert call is missing. The schema initialization logic may not execute the expected INSERT when
 the metadata table exists.

## Dependencies
None.

## Acceptance Criteria
- `task verify` passes `TestDuckDBStorageBackend::test_initialize_schema_version`.
- Schema initialization inserts the default version when absent.
- Tests document the initialization path.

## Status
Open
