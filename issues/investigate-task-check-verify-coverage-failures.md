# Investigate task check, verify, and coverage failures

## Context
`task check`, `task verify`, and `task coverage` were attempted in a fresh
environment but did not complete. The `task` command is missing, so none of
these tasks run. Executing tests directly via `uv run pytest` triggers
`ModuleNotFoundError: No module named pytest_httpx`, revealing that dev
dependencies are absent.

## Acceptance Criteria
- `task --version` succeeds.
- Dev dependencies, including `pytest_httpx`, install via setup scripts.
- `task check` completes successfully.
- `task verify` runs to completion.
- `task coverage` produces a coverage report and overall percentage.

## Status
Open
