# Status

As of **August 28, 2025**, `scripts/setup.sh` installs dependencies and records
the DuckDB VSS fallback. The current environment lacks the `task` command and
the `pytest_bdd` plugin, so Taskfile recipes and BDD tests cannot run.

## Lint, type checks, and spec tests
```text
task check
```
Result: `task` command not found.

## Unit tests
```text
uv run pytest tests/unit -q
```
Result: fails during collection with `ImportError: No module named 'pytest_bdd'`.

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
