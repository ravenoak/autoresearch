# Fix DuckDB extension download error handling

## Context
The download script uses `duckdb.IOException`, which no longer exists in recent
DuckDB releases. Tests like
`tests/unit/test_download_duckdb_extensions.py::test_download_extension_network_fallback`
raise `AttributeError`, preventing network-failure fallback logic from running.

## Dependencies
- [improve-test-coverage-and-streamline-dependencies](improve-test-coverage-and-streamline-dependencies.md)

## Acceptance Criteria
- Replace usage of `duckdb.IOException` with supported DuckDB error classes.
- Ensure network fallback loads the offline extension path without raising.
- `tests/unit/test_download_duckdb_extensions.py` passes.
- Document supported DuckDB versions in `docs/algorithms/storage.md`.

## Status
Open
