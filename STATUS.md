# Status

As of **August 27, 2025**, `scripts/setup.sh` installs dependencies and records
the DuckDB VSS fallback. The current environment lacks the `task` command, so
Taskfile recipes cannot run.

## Lint, type checks, and spec tests
```text
task check
```
Result: command not found.

## Unit tests
```text
uv sync --extra test && uv run pytest
```
Result: hangs in `redis.cluster` waiting for a Redis server. One test is
skipped and four warnings appear before the run is interrupted.

## Integration tests
```text
Integration tests did not run; unit tests did not complete.
```

## Behavior tests
```text
Behavior tests did not run; unit tests did not complete.
```

## Coverage
`task verify` cannot run without `task`. Coverage remains unavailable; the
previous baseline was **14%**, below the required 90% threshold.
