# Resolve mypy errors in orchestrator perf and search core

## Context
`task check` and `task verify` currently fail due to mypy type errors in
`src/autoresearch/orchestrator_perf.py` and `src/autoresearch/search/core.py`.
The 2025-09-14 run reported `Dict entry 3 has incompatible type 'str': 'str';`
expected `str: float` at line 137 of `orchestrator_perf.py` and an
`Argument 4 to "combine_scores" has incompatible type` error at line 661 of
`search/core.py`. These errors block the test suite from running, preventing
verification of other issues.

## Dependencies
None

## Acceptance Criteria
- `src/autoresearch/orchestrator_perf.py` passes mypy without errors.
- `src/autoresearch/search/core.py` passes mypy without errors.
- `task check` and `task verify` advance past the type-checking stage.

## Status
Open
