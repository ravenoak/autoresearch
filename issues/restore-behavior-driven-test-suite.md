# Restore behavior-driven test suite

## Context
Recent smoke runs report failing behavior-driven scenarios and `task verify`
does not exercise the `tests/behavior` suite. Without passing BDD tests,
critical user workflows, reasoning modes, and error recovery paths remain
unverified.

## Dependencies
- [add-test-coverage-for-optional-components](add-test-coverage-for-optional-components.md)

## Acceptance Criteria
- Feature files under `tests/behavior` run without failures using the base `[test]`
  extras.
- `uv run pytest tests/behavior -q` exercises `user_workflows`, `reasoning_modes`,
  and `error_recovery` markers.
- `task verify` includes the behavior suite once it passes.
- `tests/AGENTS.md` documents any new markers or extras used by behavior tests.

## Status
Open
