# Resolve current test failures

## Context
Recent test runs show multiple failures and lint issues:
- `src/autoresearch/orchestration/metrics.py:102:1: E303 too many blank lines (4)` from `uv run flake8 src tests`
- Six attribute errors in `src/autoresearch/search/core.py` from `uv run mypy src`
- Failing tests in `tests/unit/test_cache.py::test_search_uses_cache`, `tests/unit/test_cache.py::test_cache_is_backend_specific`, `tests/unit/test_failure_scenarios.py::test_external_lookup_network_failure`, `tests/unit/test_main_monitor_commands.py::test_serve_a2a_command_keyboard_interrupt`, and `tests/unit/test_metrics.py::test_metrics_collection_and_endpoint`

## Acceptance Criteria
- Flake8 runs without errors
- `uv run mypy src` completes without type errors
- `uv run pytest -q` passes with all tests succeeding

## Status
Open
