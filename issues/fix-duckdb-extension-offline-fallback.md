# Fix DuckDB extension offline fallback

## Context
`uv run pytest tests/unit/test_download_duckdb_extensions.py -q` fails on
2025-09-15. Offline fallbacks attempt to copy the stub extension over itself,
raising `shutil.SameFileError`, and the stub files retain the literal string
"stub" rather than a zero-byte placeholder. These failures break the
network-fallback flow exercised by `scripts/download_duckdb_extensions.py` and
prevent `task verify` from completing.

## Dependencies
None

## Acceptance Criteria
- `tests/unit/test_download_duckdb_extensions.py` passes, including the offline
  fallback scenarios.
- Stub artifacts created during the fallback logic are zero bytes and safe for
  smoke tests.
- Update documentation (e.g., `docs/install` or setup notes) to describe the
  corrected offline flow.

## Status
Open
