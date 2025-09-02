# Status

As of **September 24, 2025**, `task` must be installed manually. After adding
`.venv/bin` to the `PATH`, `task --version` reports `3.44.1` and `task check`
completes successfully. `task verify` still stalls during the coverage phase:
`tests/unit/distributed/test_coordination_properties.py::test_message_processing_is_idempotent`
triggers a `hypothesis.errors.DeadlineExceeded` and the command exits with
status 201, leaving coverage reports incomplete. DuckDB extension downloads
still fall back to a stub if the network is unavailable. The setup script
continues treating a missing extension as non-fatal and runs the smoke test
against the stub to verify basic functionality. Dependency pins for `fastapi`
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
`task verify` halts before these tests run.

## Behavior tests
Not executed in the current run.

## Coverage
Coverage data was not generated because `task verify` failed.

## Open issues
- [add-ranking-algorithm-proofs-and-simulations](
  issues/add-ranking-algorithm-proofs-and-simulations.md)
- [add-storage-eviction-proofs-and-simulations](
  issues/add-storage-eviction-proofs-and-simulations.md)
- [add-test-coverage-for-optional-components](
  issues/add-test-coverage-for-optional-components.md)
- [configuration-hot-reload-tests](
  issues/configuration-hot-reload-tests.md)
- [deliver-bug-fixes-and-docs-update](
  issues/deliver-bug-fixes-and-docs-update.md)
- [fix-idempotent-message-processing-deadline](
  issues/fix-idempotent-message-processing-deadline.md)
- [fix-task-verify-coverage-hang](
  issues/fix-task-verify-coverage-hang.md)
- [hybrid-search-ranking-benchmarks](
  issues/hybrid-search-ranking-benchmarks.md)
- [improve-duckdb-extension-fallback](
  issues/improve-duckdb-extension-fallback.md)
- [reach-stable-performance-and-interfaces](
  issues/reach-stable-performance-and-interfaces.md)
- [restore-task-cli-availability](
  issues/restore-task-cli-availability.md)
- [simulate-distributed-orchestrator-performance](
  issues/simulate-distributed-orchestrator-performance.md)
- [stabilize-api-and-improve-search](
  issues/stabilize-api-and-improve-search.md)
- [streaming-webhook-refinements](
  issues/streaming-webhook-refinements.md)
