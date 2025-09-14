# Resolve mypy errors in orchestrator perf and search core

## Context
`task check` and `task verify` currently fail due to mypy type errors in `src/autoresearch/orchestrator_perf.py` and `src/autoresearch/search/core.py`. These errors block the test suite from running, preventing verification of other issues.

## Dependencies
None

## Acceptance Criteria
- `src/autoresearch/orchestrator_perf.py` passes mypy without errors.
- `src/autoresearch/search/core.py` passes mypy without errors.
- `task check` and `task verify` advance past the type-checking stage.

## Status
Open
