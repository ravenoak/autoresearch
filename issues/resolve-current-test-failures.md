# Resolve current test failures

## Context
Initial test runs failed during collection due to missing dependencies.
After installing the development extras with
`uv pip install -e '.[full,dev]'`, the current state is:
- `uv run flake8 src tests` reports no issues
- `uv run mypy src` reports type errors in `autoresearch/cache.py` and
  `autoresearch/search/core.py`
- `uv run pytest -q` fails because coverage is about twenty-two percent
  while the configuration requires ninety percent

## Acceptance Criteria
- Flake8 runs without errors
- `uv run mypy src` completes without type errors
- `uv run pytest -q` passes with all tests succeeding

## Status
Open
