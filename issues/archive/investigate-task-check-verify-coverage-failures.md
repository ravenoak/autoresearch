# Investigate task check, verify, and coverage failures

## Context
`task check`, `task verify`, and `task coverage` were attempted in a fresh
environment but did not complete. The `task` command is missing, so none of
these tasks run. Executing tests directly via `uv run pytest` triggers
`ModuleNotFoundError: No module named pytest_httpx`, revealing that dev
dependencies are absent.

## Milestone

- 0.1.0a1 (2026-03-01)

## Dependencies

- [prepare-initial-alpha-release](prepare-initial-alpha-release.md)

## Acceptance Criteria
- `task --version` succeeds.
- Dev dependencies, including `pytest_httpx`, install via setup scripts.
- `task check` completes successfully.
- `task verify` runs to completion.
- `task coverage` produces a coverage report and overall percentage.

## Status
Archived
