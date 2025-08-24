# Resolve test failures and task tooling

## Context
Go Task and `redis` are installed, yet `task check` fails with `flake8`
warnings for an unused import in
`src/autoresearch/orchestration/metrics.py` and import order in
`tests/behavior/features/conftest.py`. Targeted unit tests such as
`test_monitor_cli.py::test_monitor_metrics` and
`test_token_budget_convergence.py::test_suggest_token_budget_converges`
now pass, but API authentication, concurrent query handling, Redis broker
detection, and behavior feature discovery remain unresolved.

Redis-dependent integration tests skip cleanly when `redis` is missing.

## Dependencies

- [address-storage-persistence-eviction-failure](archive/address-storage-persistence-eviction-failure.md)
- [correct-token-budget-convergence-logic](archive/correct-token-budget-convergence-logic.md)
- [repair-api-authentication-endpoints](repair-api-authentication-endpoints.md)
- [fix-concurrent-query-interface-behavior](archive/fix-concurrent-query-interface-behavior.md)
- [add-redis-dependency-for-integration-tests](add-redis-dependency-for-integration-tests.md)
- [fix-monitor-cli-metrics-failure](archive/fix-monitor-cli-metrics-failure.md)
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
