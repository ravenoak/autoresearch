# Handle DuckDB extension download errors

## Context
`scripts/download_duckdb_extensions.py` assumes `duckdb.DuckDBError` exists when
network failures occur. Current DuckDB releases raise `duckdb.Error`, causing
tracebacks and repeated retries that still leave the VSS extension absent.

## Dependencies
None

## Acceptance Criteria
- Script catches `duckdb.Error` instead of `duckdb.DuckDBError`.
- Failed downloads retry and fall back to the stub extension without stack
  traces.
- Extension load is verified on Linux and macOS.
- Unit test covers the error path.
- `docs/algorithms/storage.md` notes the fallback behavior.

## Status
Open
