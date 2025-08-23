# Resolve test failures and task tooling

## Context
The development environment lacks the `task` runner, so automated workflows
like `task check` and `task verify` cannot run. Manual checks show failing unit
and behavior tests, notably in token budget convergence and knowledge graph
persistence. Restoring the task tooling and stabilizing the tests is required
before the alpha release.

## Acceptance Criteria
- Go Task installed in `.venv` and available on `PATH`.
- `task check` and `task verify` succeed on a fresh clone.
- Unit tests pass without failures.
- Behavior test suite passes or scenarios are updated to be reliable.
- `STATUS.md` and `TASK_PROGRESS.md` document the passing test results.

## Status
Open
