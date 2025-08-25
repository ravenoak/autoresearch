# Fix storage table creation errors

## Context
Running `./.venv/bin/task check` triggers `autoresearch.errors.StorageError: Failed to create tables`
in unit tests such as `tests/unit/test_eviction.py::test_ram_eviction`. The DuckDB backend fails to
initialize required tables during tests, causing seven errors and multiple failures.

## Acceptance Criteria
- DuckDB storage setup creates required tables without raising `StorageError`.
- Unit tests relying on DuckDB run without manual setup or residual files.
- `./.venv/bin/task check` passes the affected tests.

## Status
Open
