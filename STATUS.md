# Status

As of **August 31, 2025**, the evaluation environment lacked the Go Task CLI.
Dependencies were installed with `uv sync`, but `task check` could not run and
`uv run pytest tests/unit` was interrupted after the first test, leaving overall
test and coverage status unknown. When DuckDB extensions cannot be downloaded,
setup logs a warning and skips the smoke test, falling back to a stub; see
`docs/duckdb_compatibility.md` for details. Dependency pins for `fastapi`
(>=0.115.12) and `slowapi` (==0.1.9) remain in place.

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
Not run: missing `task` CLI prevented `task check`.

## Targeted tests
Partial: `uv run pytest tests/unit` collected 805 tests; the first passed, but
the run was interrupted before `test_message_processing_is_idempotent` could
complete.

## Integration tests
Not executed.

## Behavior tests
Not executed.

## Coverage
Not reported: test run interruption prevented coverage generation.
