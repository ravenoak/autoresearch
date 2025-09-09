# Resolve package metadata warnings in check env

## Context
Running `task check` reports missing package metadata for `GitPython`,
`cibuildwheel`, `duckdb-extension-vss`, `spacy`, and several `types-*`
stubs. As of September 9, 2025, these warnings persist despite earlier
fixes and should be eliminated for a clean environment check.

## Dependencies
None.

## Acceptance Criteria
- `uv run python scripts/check_env.py` runs without package metadata warnings.
- Document any required extras or steps in `STATUS.md`.

## Status
Open
