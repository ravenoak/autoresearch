# Resolve test failures and task tooling

## Context
Go Task is still unavailable on `PATH`, so repository tasks cannot run
directly. After installing minimal development extras, `flake8`, `mypy`,
spec checks, and a subset of unit tests pass. Running the full test suite
reveals failures in storage persistence eviction, token budget convergence,
API authentication, and concurrent query handling.

## Dependencies

- [address-storage-persistence-eviction-failure](address-storage-persistence-eviction-failure.md)
- [correct-token-budget-convergence-logic](correct-token-budget-convergence-logic.md)
- [repair-api-authentication-endpoints](repair-api-authentication-endpoints.md)
- [fix-concurrent-query-interface-behavior](fix-concurrent-query-interface-behavior.md)

## Acceptance Criteria
- Go Task installed in `.venv` and available on `PATH`.
- `task check` and `task verify` succeed on a fresh clone.
- Unit tests pass without failures.
- Behavior test suite passes or scenarios are updated to be reliable.
- `STATUS.md` and `TASK_PROGRESS.md` document the passing test results.

## Status
Open
