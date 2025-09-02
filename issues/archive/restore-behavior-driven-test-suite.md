# Restore behavior-driven test suite

## Context
Running `uv run pytest` previously failed with
`ModuleNotFoundError: No module named 'pytest_bdd'`. After adding the plugin
and missing step definitions, `uv run pytest tests/behavior -q` now passes and
`task verify` includes the behavior suite.

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
Archived
