# Lint errors in stub modules

## Context
Running `uv run flake8 src tests` and `uv run ruff check --fix src tests` after installing development extras previously revealed
lint violations. `ruff` reported `E402` in `src/autoresearch/visualization.py`, and flake8 flagged `E701` in `tests/stubs/a2a.py`.

After fixing the import order in `src/autoresearch/orchestration/orchestration_utils.py` and reinstalling dev dependencies,
`uv run ruff check src tests` and `uv run flake8 src tests` now pass without errors. The test suite still fails because the
coverage threshold is not met and broader orchestrator tests error, so `task verify` remains blocked by
[`unit-tests-after-orchestrator-refactor.md`](unit-tests-after-orchestrator-refactor.md).

## Acceptance Criteria
- `ruff check` and `flake8` run cleanly.
- `task verify` succeeds once lint issues are fixed.

## Status
Archived
