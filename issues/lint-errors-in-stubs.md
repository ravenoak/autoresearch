# Lint errors in stub modules

## Context
Running `uv run flake8 src tests` and `uv run ruff check --fix src tests` after installing development extras reveals unresolved
lint violations. `ruff` reports `E402` in `src/autoresearch/visualization.py`, and flake8 flags `E701` in `tests/stubs/a2a.py`.
After reordering imports in `visualization.py`, `ruff check src/autoresearch/visualization.py` passes. A fresh `flake8 src tests`
run does not reproduce the earlier `E701` warning in `tests/stubs/a2a.py`. However, `uv run pytest` continues to fail because
coverage remains below the required threshold.

## Acceptance Criteria
- `ruff check` and `flake8` run cleanly.
- `task verify` succeeds once lint issues are fixed.

## Status
Open
