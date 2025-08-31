# Status

As of **September 15, 2025**, the environment installs the Go Task CLI and
optional extras. `task check` passes, but `task verify` stalled during the
coverage step after syncing all extras. The run exited after a manual
interrupt, leaving coverage data unreported. When DuckDB extensions cannot be
downloaded, setup logs a warning and skips the smoke test, falling back to a
stub; see `docs/duckdb_compatibility.md` for details. Dependency pins for
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
Passed via `task check`.

## Targeted tests
Fail: `test_message_processing_is_idempotent` exceeded its Hypothesis deadline.

## Integration tests
Not executed.

## Behavior tests
Fail: missing step definitions in 19 scenarios; suite not executed in latest run.

## Coverage
Not reported: coverage run stalled and was interrupted; previous targeted
modules were **100%** (57/57 lines).
