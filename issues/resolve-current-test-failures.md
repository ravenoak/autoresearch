# Resolve current test failures

## Context
Recent checks show linting and type checking succeed, but the full test
suite still fails and coverage remains below the required threshold:
- `uv run flake8 src tests` reports no issues
- `uv run mypy src` completes without errors
- `uv run pytest -q` exits with 52 failures across search, API, and
  orchestrator scenarios

## Acceptance Criteria
- Flake8 runs without errors
- `uv run mypy src` completes without type errors
- `uv run pytest -q` passes with all tests succeeding and required coverage

## Status
Open
