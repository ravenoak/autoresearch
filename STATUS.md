# Status

As of **September 1, 2025**, `scripts/setup.sh` reports Go Task `3.44.1` and
`uv run task check` completes successfully. `uv run task verify` now finishes
in under fifteen minutes on a clean environment. DuckDB extension downloads
still fall back to a stub if the network is unavailable. The setup script
treats a missing extension as non-fatal and runs the smoke test against the
stub to verify basic functionality. Dependency pins for `fastapi`
(>=0.115.12) and `slowapi` (==0.1.9) remain in place.

References to pre-built wheels for GPU-only packages live under `wheels/gpu`.
`task verify` skips these dependencies by default; set `EXTRAS=gpu` when GPU
features are required. Setup helpers and Taskfile commands consult this
directory automatically when GPU extras are installed.

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
`uv run task check` executes flake8, mypy, and spec tests; all pass.

## Targeted tests
The minimal unit subset used by `task check` passes (8 tests).

## Integration tests
Not executed.

## Behavior tests
Not executed.

## Coverage
Targeted modules report **100%** line coverage (57/57 lines).

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
- [fix-idempotent-message-processing-deadline](
  issues/fix-idempotent-message-processing-deadline.md)
- [resolve-pre-alpha-release-blockers](
  issues/resolve-pre-alpha-release-blockers.md)
- [add-ranking-algorithm-proofs-and-simulations](
  issues/add-ranking-algorithm-proofs-and-simulations.md)
- [simulate-distributed-orchestrator-performance](
  issues/simulate-distributed-orchestrator-performance.md)
