# Status

As of **August 31, 2025**, the environment now installs the Go Task CLI and
optional extras. Dependency pins for `fastapi` (>=0.115.12) and `slowapi`
(==0.1.9) remain in place. `task check` passes, but `task verify` fails:
19 behavior-driven tests lack step definitions, so coverage only reflects the
57 statements in targeted modules. When DuckDB extensions cannot be downloaded,
setup now logs a warning and skips the smoke test, falling back to a stub; see
`docs/duckdb_compatibility.md` for details.

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
Passed during `task verify`.

## Integration tests
Not executed.

## Behavior tests
Fail: missing step definitions in 19 scenarios.

## Coverage
**100%** (57/57 lines) for targeted modules; behavior tests remain missing.
