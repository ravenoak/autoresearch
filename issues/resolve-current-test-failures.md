# Resolve current test failures

## Context
Recent test runs with `uv run pytest -q` are interrupted after 4 failures
caused by `Search.calculate_bm25_scores` missing a required positional
argument. The partial run reports 362 passed, 8 skipped, 97 deselected and
30 warnings. The project cannot reach the planned **0.1.0** release until
the suite is green and coverage meets expectations.

## Acceptance Criteria
- All tests pass with `uv run pytest -q`.
- `uv run pytest --cov=src` reports at least 90% coverage.
- The suite runs without unexpected warnings.

## Status
Open

