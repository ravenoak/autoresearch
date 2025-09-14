# Fix storage integration test failures

## Context
Recent full-suite testing (`uv run pytest`) revealed multiple failures in storage-related integration tests. Problems span `tests/integration/test_storage_concurrency.py::test_concurrent_writes`, several cases in `tests/integration/test_storage_eviction_sim.py`, `tests/integration/test_storage_schema.py::test_initialize_schema_version_without_fetchone`, and `tests/integration/test_storage_duckdb_fallback.py::test_ram_budget_benchmark`. These issues block the v0.1.0a1 release.

## Dependencies
None.

## Acceptance Criteria
- `pytest tests/integration/test_storage_*` runs without failures.
- `task verify` (or equivalent) completes storage integration tests successfully.
- Document fixes in the changelog.

## Status
Archived
