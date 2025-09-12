# Resolve resource tracker errors in verify

## Context
`task verify` previously exited with multiprocessing resource tracker
`KeyError` messages after unit tests, preventing integration tests and
coverage from completing.

On September 6, 2025, the error was not reproduced because the run aborted on
other failing tests before reaching integration scenarios.

On September 12, 2025, `task verify` again emitted `KeyError: '/mp-...'` after
`tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_initialize_schema_version`
failed, leaving coverage incomplete.

Auditing fixtures that spawn multiprocessing pools and queues shows they call
`close()` and `join_thread()` to avoid leaking resources.

## Dependencies
- [fix-duckdb-storage-schema-initialization](fix-duckdb-storage-schema-initialization.md)

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open
