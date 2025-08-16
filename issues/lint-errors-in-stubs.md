# Lint errors in stub modules

## Context
Running `uv run flake8 src tests` and `uv run ruff check --fix src tests` after installing development extras reveals unresolved lint violations. `ruff` reports `E402` in `src/autoresearch/visualization.py`, and flake8 flags `E701` in `tests/stubs/a2a.py`.

## Acceptance Criteria
- `ruff check` and `flake8` run cleanly.
- `task verify` succeeds once lint issues are fixed.

## Status
Open
