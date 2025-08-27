# Status

As of **August 27, 2025**, `scripts/codex_setup.sh` followed by
`uv sync --extra dev --extra test` installs dependencies and exposes the
`task` command. `task check` launches but the unit suite runs slowly and was
interrupted after exceeding the allotted runtime.

## Lint, type checks, and spec tests
```text
task check
```
Result: lint and type checks passed; unit tests were interrupted after an
extended run.

## Unit tests
Sample failing tests when run individually:
- `tests/unit/test_cli_backup_extra.py::test_backup_restore_error`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_setup_with_default_path`

## Integration tests
```text
Integration tests did not run; unit tests failing.
```

## Behavior tests
```text
Behavior tests did not run; unit tests failing.
```

## Coverage
Coverage remains unavailable because `task check` did not complete. The previous
baseline was **14%**, below the required 90% threshold.
