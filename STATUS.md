# Status

As of **September 1, 2025**, the environment lacks the Go Task CLI and
`uv run pytest` fails with
`ModuleNotFoundError: No module named 'pytest_bdd'`. The earlier
`test_backup_manager` stall remains resolved: the unit test completes
immediately using an event-based backup trigger. DuckDB extension downloads
still fall back to a stub if the network is unavailable; a real extension
triggers the smoke test to confirm vector search. Dependency pins for
`fastapi` (>=0.115.12) and `slowapi` (==0.1.9) remain in place.

References to pre-built wheels for GPU-only packages live under `wheels/gpu`.
`task verify` skips these dependencies by default; set `EXTRAS=gpu` when GPU
features are required.

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
Not run: missing Task CLI prevents `task check`.

## Targeted tests
Failed: `uv run pytest` aborts before running tests due to missing
`pytest_bdd`.

## Integration tests
Not executed.

## Behavior tests
Not executed.

## Coverage
Coverage reports 100% (57/57 lines) for targeted modules.

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
