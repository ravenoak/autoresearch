# Restore behavior-driven test suite

## Context
Running `uv run pytest` currently fails with
`ModuleNotFoundError: No module named 'pytest_bdd'`. After installing this
plugin, `task verify` reports 42 failing scenarios across
`error_recovery_workflow_steps.py`, `first_run_steps.py`, `gui_cli_steps.py`,
`hybrid_search_steps.py`, `interactive_monitor_steps.py`,
`interface_test_cli_steps.py`, `mcp_interface_steps.py`,
`orchestration_system_steps.py`, and others. Many step definitions are
missing so the behavior suite aborts before coverage is recorded. Without
passing BDD tests, critical user workflows, reasoning modes, and error
recovery paths remain unverified.

On **August 31, 2025**, `task coverage` stopped during unit tests and never
reached the behavior suite, so the step-definition gaps persist.

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
