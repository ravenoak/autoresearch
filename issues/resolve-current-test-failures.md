# Resolve current test failures

## Context
Recent checks show linting and type checking pass, but tests fail during
collection:
- `uv run flake8 src tests` reports no issues
- `uv run mypy src` succeeds
- `uv run pytest -q` fails with `ModuleNotFoundError` for dependencies such
  as `tomli_w`, `freezegun`, `hypothesis`, and `pytest_bdd`

## Acceptance Criteria
- Flake8 runs without errors
- `uv run mypy src` completes without type errors
- `uv run pytest -q` passes with all tests succeeding

## Status
Open
