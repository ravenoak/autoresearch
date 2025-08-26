# Stabilize CLI and backup tests

## Context
`uv run pytest tests/unit -q` shows 31 failures, many in CLI help, backup,
and monitor command tests. Exit codes are non-zero and DuckDB tables are
missing, raising `StorageError`.

## Milestone

- 0.1.0a1 (2026-04-15)

## Dependencies

- [resolve-storage-layer-test-failures](../resolve-storage-layer-test-failures.md)

## Acceptance Criteria
- CLI help and option tests under `tests/unit/test_cli_*` and `tests/unit/test_main_*` pass.
- Backup command tests in `tests/unit/test_main_backup_commands.py` pass, including error paths.
- Test harness initializes DuckDB tables for CLI tests.
- `task check` can run unit suite without CLI failures.

## Status
Archived
