# Resolve current test failures

## Context
Recent checks show linting passes, but type checking and coverage fail:
- `uv run flake8 src tests` reports no issues
- `uv run mypy src` reports 10 errors
- `uv run pytest tests/unit/test_failure_scenarios.py` passes tests but fails
  coverage with total 21% < required 90%

## Acceptance Criteria
- Flake8 runs without errors
- `uv run mypy src` completes without type errors
- `uv run pytest -q` passes with all tests succeeding and required coverage

## Status
Open
