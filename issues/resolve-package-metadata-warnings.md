# Resolve package metadata warnings in check env

## Context
Running `task check` reports missing package metadata for `GitPython`,
`cibuildwheel`, `duckdb-extension-vss`, `spacy`, and several `types-*`
stubs. As of September 9, 2025, `uv run python scripts/check_env.py`
aborts early with `ERROR: Go Task 3.0.0+ is required`, so these warnings
cannot be evaluated. The script should run to completion without
emitting package metadata warnings.

## Dependencies
None.

## Acceptance Criteria
- `uv run python scripts/check_env.py` runs without package metadata warnings.
- Document any required extras or steps in `STATUS.md`.

## Status
Open
