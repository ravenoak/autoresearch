# Status

As of **September 1, 2025**, the Go Task CLI is available and `task check`
passes in a clean environment. `task verify` still fails during the coverage
step, consistent with the open coverage-hang issue. The earlier
`test_backup_manager` stall remains resolved: the unit test completes
immediately using an event-based backup trigger. DuckDB extension downloads
still fall back to a stub if the network is unavailable; a real extension
triggers the smoke test to confirm vector search. Dependency pins for
`fastapi` (>=0.115.12) and `slowapi` (==0.1.9) remain in place.

References to pre-built wheels for GPU-only packages live under `wheels/gpu`.
`task verify` skips these dependencies by default; set `EXTRAS=gpu` when GPU
features are required.

## Lint, type checks, and spec tests
Passed: `task check`.

## Targeted tests
Failed: `task verify` aborts during coverage.

## Integration tests
Not executed: `task verify` aborts during coverage.

## Behavior tests
Not executed: `task verify` aborts during coverage.

## Coverage
Unavailable: `task verify` aborts during coverage.

## Open issues
- [restore-task-cli-availability](
  issues/restore-task-cli-availability.md)
- [restore-behavior-driven-test-suite](
  issues/restore-behavior-driven-test-suite.md)
- [add-test-coverage-for-optional-components](
  issues/add-test-coverage-for-optional-components.md)
- [address-task-verify-dependency-builds](
  issues/address-task-verify-dependency-builds.md)
- [fix-task-verify-package-metadata-errors](
  issues/fix-task-verify-package-metadata-errors.md)
- [fix-task-verify-coverage-hang](
  issues/fix-task-verify-coverage-hang.md)
- [fix-idempotent-message-processing-deadline](
  issues/fix-idempotent-message-processing-deadline.md)
- [resolve-pre-alpha-release-blockers](
  issues/resolve-pre-alpha-release-blockers.md)
- [add-ranking-algorithm-proofs-and-simulations](
  issues/add-ranking-algorithm-proofs-and-simulations.md)
- [simulate-distributed-orchestrator-performance](
  issues/simulate-distributed-orchestrator-performance.md)
