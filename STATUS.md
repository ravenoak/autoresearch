# Status

As of **September 2, 2025**, `scripts/setup.sh` installs the Go Task CLI and
syncs optional extras. `task check` passes, but `task verify` fails during
`flake8` due to a trailing blank line in
`tests/integration/test_storage_eviction_sim.py:47`. Coverage remains
unavailable. Dependency pins for `fastapi` (>=0.115.12) and `slowapi` (==0.1.9)
remain in place.

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

## Offline DuckDB extension

`scripts/setup.sh` now continues when the VSS extension download fails. It
records a zero-byte stub at `extensions/vss/vss.duckdb_extension` and proceeds
with smoke tests, allowing offline environments to initialize without vector
search.

## Lint, type checks, and spec tests
`task check` completed successfully.

## Targeted tests
`tests/unit/test_version.py` and `tests/unit/test_cli_help.py` passed under
`task check`.

## Integration tests
Not executed.

## Behavior tests
Not executed.

## Coverage
Coverage was not generated; `task verify` exited during linting.

## Open issues
- [add-storage-eviction-proofs-and-simulations](
  issues/add-storage-eviction-proofs-and-simulations.md)
- [add-test-coverage-for-optional-components](
  issues/add-test-coverage-for-optional-components.md)
- [fix-task-verify-coverage-hang](
  issues/fix-task-verify-coverage-hang.md)
- [improve-duckdb-extension-fallback](
  issues/improve-duckdb-extension-fallback.md)
- [prepare-v0-1-0a1-release](
  issues/prepare-v0-1-0a1-release.md)
- [reach-stable-performance-and-interfaces](
  issues/reach-stable-performance-and-interfaces.md)
- [resolve-llm-extra-installation-failure](
  issues/resolve-llm-extra-installation-failure.md)
- [simulate-distributed-orchestrator-performance](
  issues/simulate-distributed-orchestrator-performance.md)
- [stabilize-api-and-improve-search](
  issues/stabilize-api-and-improve-search.md)
