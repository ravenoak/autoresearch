# Status

As of **August 31, 2025**, the environment now installs the Go Task CLI and
optional extras. `task check` passes, but `task verify` fails: 19
behavior-driven tests lack step definitions, so coverage is not reported.
If DuckDB extensions cannot be downloaded, setup falls back to a stub and
skips smoke tests; see `docs/duckdb_compatibility.md` for details.

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
