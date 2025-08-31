# Status

As of **August 31, 2025**, the environment now installs the Go Task CLI and
optional extras. `task check` passes, but `task verify` fails: 19
behavior-driven tests lack step definitions, so coverage is not reported.

## Bootstrapping without Go Task

If the Go Task CLI cannot be installed, set up the environment with:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[test]"
uv run scripts/download_duckdb_extensions.py --output-dir ./extensions
```

This installs the `[test]` extras and records the DuckDB VSS extension path so
`uv run pytest` works without `task`.

## Lint, type checks, and spec tests
Passed via `task check`.

## Targeted tests
Passed during `task verify`.

## Integration tests
Not executed.

## Behavior tests
Fail: missing step definitions in 19 scenarios.

## Coverage
Unavailable while behavior tests fail.
