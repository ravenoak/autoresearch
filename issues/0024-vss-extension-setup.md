# Issue 24: Fix VSS extension and smoke test failures

The environment smoke test fails because the VSS DuckDB extension is missing or
invalid. `matplotlib` is now installed, but the missing extension still leaves
`CODEX_ENVIRONMENT_SETUP_FAILED` in the repository.

## Context
`scripts/smoke_test.py` reports:
- `Failed to load VSS extension from configured path`

## Acceptance Criteria
- Provide a valid VSS extension or adjust the setup to skip the check when the extension is unavailable.
- Confirm `matplotlib` remains installed by default so the smoke test passes.
- Update setup scripts and documentation accordingly.

## Status
Closed – smoke test skips the VSS check when the extension is
unavailable and removes the `CODEX_ENVIRONMENT_SETUP_FAILED` marker.
Resolved in commit 1be9671 and the follow-up commit in this branch.

## Related
- #23
