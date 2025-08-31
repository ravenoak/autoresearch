# Restore behavior-driven test suite

## Context
Running `uv run pytest` currently fails with
`ModuleNotFoundError: No module named 'pytest_bdd'`. After installing this
plugin, `task verify` reports 19 failing scenarios across
`api_batch_query_steps.py`, `api_async_query_steps.py`, `search_cli_steps.py`,
`monitor_cli_steps.py`, and `query_interface_steps.py`. Many step definitions
are missing so the behavior suite aborts before coverage is recorded.
Without passing BDD tests, critical user workflows, reasoning modes, and
error recovery paths remain unverified.

## Dependencies
- [add-test-coverage-for-optional-components](add-test-coverage-for-optional-components.md)

## Acceptance Criteria
- Implement missing step definitions so features in
  `tests/behavior/steps/` run without failures using the base `[test]` extra.
- `uv run pytest tests/behavior -q` exercises `user_workflows`,
  `reasoning_modes`, and `error_recovery` markers.
- `task verify` includes the behavior suite once it passes.
- `tests/AGENTS.md` documents any new markers or extras used by behavior tests.

## Status
Open
