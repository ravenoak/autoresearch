# Resolve storage persistence test failure

## Context
`tests/unit/test_storage_persistence.py::
test_initialize_creates_tables_and_teardown_removes_file`
currently fails with `assert False`, indicating the persistence layer does not
create tables or clean up files as expected.
As of 2025-09-12 the test run logs repeated DuckDB VSS extension download
warnings and shows `_create_tables` never invoked, leaving the `called` flag
unset.

## Dependencies
None

## Acceptance Criteria
- `task verify` passes
  `tests/unit/test_storage_persistence.py::
  test_initialize_creates_tables_and_teardown_removes_file`.
- Storage initialization creates required tables and teardown removes artifacts.
- Regression test documents the corrected behavior.

## Status
Archived
