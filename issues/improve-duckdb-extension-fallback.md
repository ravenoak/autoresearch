# Improve duckdb extension fallback

## Context
`scripts/setup.sh` fails when the DuckDB VSS extension cannot be downloaded.
Although a stub is created, the smoke test still aborts, leaving setup
incomplete.

## Dependencies
None.

## Acceptance Criteria
- `scripts/setup.sh` completes successfully when the VSS extension download
  fails or the network is unavailable.
- Smoke tests pass using the offline stub.
- Document offline extension fallback behavior in `STATUS.md` or docs.

## Status
Open
