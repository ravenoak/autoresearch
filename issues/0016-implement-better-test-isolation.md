# Issue 16: Implement better test isolation

Track the task "Implement better test isolation" from Phase 2 of `TASK_PROGRESS.md`.
See [TASK_PROGRESS.md](../TASK_PROGRESS.md) for overall status.

## Context
Ensure tests run independently without shared state or side effects.

## Acceptance Criteria
- Fixtures clean up after tests
- Tests parallelize without interference
- Shared resources isolated

## Status
In progress – see tests/conftest.py

## Related
- #14
