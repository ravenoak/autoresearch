# Issue 1: Complete cross-component integration tests

Track the task "Complete cross-component integration tests" from Phase 2 of `TASK_PROGRESS.md`.
See [TASK_PROGRESS.md](../TASK_PROGRESS.md) for overall status.

## Context
Implement integration tests that exercise orchestrator, agent, storage,
and search components together to validate end-to-end behavior.

## Acceptance Criteria
- Tests cover interactions among orchestrator, agents, storage, and search
- Realistic user flows are executed across components
- Integration suite runs in CI

## Status
In progress – basic coverage via
tests/integration/test_orchestrator_search_storage.py is **Done**.
Outstanding: add full end-to-end scenarios and integrate the suite into CI.

## Related
- #2
- #3
- #4
- #5
- #6
- #7
- #8
- #9
