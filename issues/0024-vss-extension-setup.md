# Issue 24: Fix VSS extension and smoke test failures

The environment smoke test fails because the VSS DuckDB extension stub is
invalid. `matplotlib` is now installed, but the missing extension still leaves
`CODEX_ENVIRONMENT_SETUP_FAILED` in the repository.

## Context
`scripts/smoke_test.py` reports:
- `Failed to load VSS extension from ./extensions/vss_stub.duckdb_extension`

## Acceptance Criteria
- Provide a valid VSS extension or adjust the setup to skip the check when the extension is unavailable.
- Confirm `matplotlib` remains installed by default so the smoke test passes.
- Update setup scripts and documentation accordingly.

## Status
Open

## Related
- #23
