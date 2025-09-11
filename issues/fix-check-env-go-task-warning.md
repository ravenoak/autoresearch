# Fix check env Go Task warning

## Context
`tests/unit/test_check_env_warnings.py::test_missing_go_task_warns` fails because
`check_env.check_task` logs a message instead of emitting a `UserWarning` when
Go Task is absent. The test expects a warning to guide users.

## Dependencies
None.

## Acceptance Criteria
- `check_env.check_task` raises a `UserWarning` when Go Task is missing or the test is updated accordingly.
- `tests/unit/test_check_env_warnings.py::test_missing_go_task_warns` passes.
- `uv run python scripts/check_env.py` warns when Go Task is unavailable.

## Status
Open
