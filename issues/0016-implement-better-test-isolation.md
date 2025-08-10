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
In progress – fixtures added, but parallel test run shows multiple failures

## Next steps
- Investigate failing unit tests uncovered by parallel execution
- Address outstanding failures before closing #16
- Review isolation status after fixes

## Related
- #14
