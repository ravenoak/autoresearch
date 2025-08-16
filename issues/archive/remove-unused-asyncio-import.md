# Remove unused asyncio import

Track the gap "flake8 fails due to unused asyncio import" discovered during testing.

## Context
Running `task verify` fails at the flake8 step with `tests/behavior/steps/api_async_query_steps.py:5:1: F401 'asyncio' imported but unused`.

## Acceptance Criteria
- Remove or use the `asyncio` import in `tests/behavior/steps/api_async_query_steps.py`
- `task verify` passes flake8 stage

## Status
Archived

