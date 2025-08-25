# Resolve test failures and task tooling

## Context
Go Task and `redis` install correctly, and linting and type checks pass. However
`task check` still reports 34 failing tests and seven errors. Failures include
DuckDB table creation errors, monitor command failures, TypeErrors in metrics
tests, missing CLI help options, broken backup subcommands, and incorrect token
budget history logic. Behavior feature discovery and API authentication remain
unresolved.

Redis-dependent integration tests skip cleanly when `redis` is missing.

## Dependencies
- [address-storage-persistence-eviction-failure](archive/address-storage-persistence-eviction-failure.md)
- [correct-token-budget-convergence-logic](archive/correct-token-budget-convergence-logic.md)
- [repair-api-authentication-endpoints](repair-api-authentication-endpoints.md)
- [fix-concurrent-query-interface-behavior](archive/fix-concurrent-query-interface-behavior.md)
- [add-redis-dependency-for-integration-tests](add-redis-dependency-for-integration-tests.md)
- [fix-metrics-summary-type-errors](fix-metrics-summary-type-errors.md)
- [fix-monitor-cli-metrics-failure](archive/fix-monitor-cli-metrics-failure.md)
- [fix-pytest-bdd-feature-discovery](fix-pytest-bdd-feature-discovery.md)
- [fix-storage-table-creation-errors](fix-storage-table-creation-errors.md)
- [repair-cli-help-and-backup-commands](repair-cli-help-and-backup-commands.md)
- [repair-monitor-serve-command](repair-monitor-serve-command.md)
- [correct-token-budget-history-logic](correct-token-budget-history-logic.md)

## Acceptance Criteria
- Go Task installed in `.venv` and available on `PATH`.
- `task check` and `task verify` succeed on a fresh clone.
- Unit tests pass without failures.
- Integration tests run or skip cleanly without missing dependencies.
- Behavior test suite passes or scenarios are updated to be reliable.
- `STATUS.md` and `TASK_PROGRESS.md` document the passing test results.

## Status
Open
