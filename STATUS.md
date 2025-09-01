# Status

As of **September 1, 2025**, the environment includes the Go Task CLI and the
`test_backup_manager` stall has been resolved. The unit test now completes
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
Not run: `task check` was skipped to conserve time.

## Targeted tests
Partial: `test_backup_scheduler_start_stop` now passes; full suite not
executed due to time limits.

## Integration tests
Not executed.

## Behavior tests
Not executed.

## Coverage
Not reported: `task coverage` exceeded the evaluation time.
