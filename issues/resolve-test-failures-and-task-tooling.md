# Resolve test failures and task tooling

## Context
 Go Task now installs correctly, and `redis` is installed, but `task check`
 reports new unit test failures. With minimal development extras, `flake8`,
 `mypy`, spec checks, and most unit tests pass. Running the full test suite
 reveals failures in storage persistence eviction, token budget convergence,
 API authentication, concurrent query handling, Redis broker detection, and
 monitor CLI metrics. Integration and behavior test suites remain unreliable.

## Dependencies

- [address-storage-persistence-eviction-failure](archive/address-storage-persistence-eviction-failure.md)
- [correct-token-budget-convergence-logic](correct-token-budget-convergence-logic.md)
- [repair-api-authentication-endpoints](repair-api-authentication-endpoints.md)
- [fix-concurrent-query-interface-behavior](archive/fix-concurrent-query-interface-behavior.md)
- [add-redis-dependency-for-integration-tests](add-redis-dependency-for-integration-tests.md)
- [fix-monitor-cli-metrics-failure](fix-monitor-cli-metrics-failure.md)
- [fix-pytest-bdd-feature-discovery](fix-pytest-bdd-feature-discovery.md)

## Acceptance Criteria
- Go Task installed in `.venv` and available on `PATH`.
- `task check` and `task verify` succeed on a fresh clone.
- Unit tests pass without failures.
- Integration tests run or skip cleanly without missing dependencies.
- Behavior test suite passes or scenarios are updated to be reliable.
- `STATUS.md` and `TASK_PROGRESS.md` document the passing test results.

## Status
Open
