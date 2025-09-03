# Status

As of **September 3, 2025**, `scripts/setup.sh` installs the Go Task CLI and
syncs optional extras. `task check` passes. A full
`uv run --all-extras task verify` attempt began downloading large GPU
dependencies and was aborted. With test extras only, the fixed
`tests/unit/distributed/test_coordination_properties.py` now runs without the
previous `tmp_path` `KeyError`. Dependency pins for `fastapi` (>=0.115.12) and
`slowapi` (==0.1.9) remain in place.

The `[llm]` extra now installs CPU-friendly libraries (`fastembed`, `dspy-ai`)
to avoid CUDA-heavy downloads. `task verify EXTRAS="llm"` succeeds with these
lighter dependencies.

The evaluation setup makes Task CLI version 3.44.1 available (`task --version`).

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
Targeted coverage for `tests/unit/distributed/test_coordination_properties.py`
completed, reporting **32%** combined coverage for
`src/autoresearch/orchestration/budgeting.py` and
`src/autoresearch/search/http.py`.

`task verify` was updated to install all extras and run marked tests. An
attempt to execute the full suite with coverage encountered failing
integration tests and did not produce a final report.

## Open issues
- [add-storage-eviction-proofs-and-simulations](
  issues/add-storage-eviction-proofs-and-simulations.md)
- [add-test-coverage-for-optional-components](
  issues/add-test-coverage-for-optional-components.md)
- [fix-task-verify-coverage-hang](
  issues/fix-task-verify-coverage-hang.md)
- [prepare-v0-1-0a1-release](
  issues/prepare-v0-1-0a1-release.md)
- [reach-stable-performance-and-interfaces](
  issues/reach-stable-performance-and-interfaces.md)
- [simulate-distributed-orchestrator-performance](
  issues/simulate-distributed-orchestrator-performance.md)
- [stabilize-api-and-improve-search](
  issues/stabilize-api-and-improve-search.md)
- [add-distributed-coordination-proofs-and-benchmarks](
  issues/add-distributed-coordination-proofs-and-benchmarks.md)
