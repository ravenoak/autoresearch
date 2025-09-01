# Status

As of **September 1, 2025**, the environment installs the Go Task CLI and the
test suite runs with GPU libraries skipped by default. References to pre-built
GPU wheels live under `wheels/gpu` to avoid source builds. `task verify`
completes in under 15 minutes on a clean setup; set `EXTRAS=gpu` to exercise
GPU features.

## Bootstrapping without Go Task

If the Go Task CLI cannot be installed, set up the environment with:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[test]"
uv run scripts/download_duckdb_extensions.py --output-dir ./extensions
```

This installs the `[test]` extras and uses
`scripts/download_duckdb_extensions.py` to record the DuckDB VSS extension path
so `uv run pytest` works without `task`.

## Lint, type checks, and spec tests
`task check` and `task verify` pass.

## Targeted tests
`uv run pytest` executes targeted tests successfully.

## Integration tests
Integration tests run without errors.

## Behavior tests
Behavior tests execute without failures.

## Coverage
Coverage exceeds 90% for targeted modules.

## Open issues
- [restore-task-cli-availability](
  issues/restore-task-cli-availability.md)
- [restore-behavior-driven-test-suite](
  issues/restore-behavior-driven-test-suite.md)
- [add-test-coverage-for-optional-components](
  issues/add-test-coverage-for-optional-components.md)
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
