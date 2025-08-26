# Resolve storage layer test failures

## Context
Recent unit, integration, and behavior test runs all fail with
`autoresearch.errors.StorageError: Failed to create tables`.
The test harness does not initialize the DuckDB-backed storage
schema, preventing higher level components from executing.
The latest unit suite shows repeated failures in
`tests/unit/test_eviction.py` and `tests/unit/test_storage_utils.py`,
confirming the schema initialization gap.

## Acceptance Criteria
- DuckDB storage tables are created automatically for tests.
- Unit tests in `tests/unit` no longer raise `StorageError`.
- Integration and behavior tests either pass or skip gracefully
  when storage is unavailable.
- Documentation updated with any new setup requirements.

## Status
Open
