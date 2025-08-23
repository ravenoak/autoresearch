# Resolve test failures and task tooling

## Context
Go Task is still unavailable on `PATH`, so repository tasks cannot run
directly. Attempting to bootstrap with `scripts/setup.sh` triggered
multi-hundred-megabyte downloads for packages such as `torch`,
`nvidia-cublas-cu12`, and `nvidia-cudnn-cu12` before installing basic
tools, and the process was terminated early. As a result `flake8`, `mypy`,
spec checks, and a subset of unit tests cannot run. Existing test failures
cover storage persistence eviction, token budget convergence, API
authentication, and concurrent query handling.

## Dependencies

- [address-storage-persistence-eviction-failure](address-storage-persistence-eviction-failure.md)
- [correct-token-budget-convergence-logic](correct-token-budget-convergence-logic.md)
- [repair-api-authentication-endpoints](repair-api-authentication-endpoints.md)
- [fix-concurrent-query-interface-behavior](fix-concurrent-query-interface-behavior.md)
- [streamline-dev-environment-setup](streamline-dev-environment-setup.md)

## Acceptance Criteria
- Go Task installed in `.venv` and available on `PATH`.
- `task check` and `task verify` succeed on a fresh clone.
- Unit tests pass without failures.
- Behavior test suite passes or scenarios are updated to be reliable.
- `STATUS.md` and `TASK_PROGRESS.md` document the passing test results.

## Status
Open
