# Resolve current test failures

## Context
Recent test runs with `uv run pytest -q` are interrupted after 4 failures
caused by `Search.calculate_bm25_scores` missing a required positional
argument. The partial run reports 362 passed, 8 skipped, 97 deselected and
30 warnings. The project cannot reach the planned **0.1.0** release until
the suite is green and coverage meets expectations.

On 2025-08-18, `uv run pytest -q` again halted with four failures:
`tests/unit/test_cache.py::test_search_uses_cache`,
`tests/unit/test_cache.py::test_cache_is_backend_specific`,
`tests/unit/test_cache.py::test_context_aware_query_expansion_uses_cache`,
and `tests/unit/test_monitor_cli.py::test_monitor_prompts_and_passes_callbacks`.
Running `uv run pytest --cov=src --cov-report=term-missing` stopped after
similar failures and did not report overall coverage.

## Acceptance Criteria
- All tests pass with `uv run pytest -q`.
- `uv run pytest --cov=src` reports at least 90% coverage.
- The suite runs without unexpected warnings.

## Status
Archived

