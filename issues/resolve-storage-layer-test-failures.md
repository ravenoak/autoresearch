# Resolve storage layer test failures

## Context
Recent test runs report assertion failures in
`tests/unit/test_duckdb_storage_backend.py` and related modules. Schema
version initialization returns unexpected values, and storage cleanup does not
match expectations. These failures block higher level components from
executing and indicate the DuckDB-backed storage layer is not configured
correctly.

## Dependencies

- None

## Acceptance Criteria
- DuckDB storage tables and schema versions are initialized deterministically
  for tests.
- Unit tests in `tests/unit` no longer fail due to version mismatches or
  improper close semantics.
- Integration and behavior tests either pass or skip gracefully
  when storage is unavailable.
- Documentation updated with any new setup requirements.

## Status
Open
