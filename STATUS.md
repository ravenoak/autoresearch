# Status

As of **August 27, 2025**, `scripts/setup.sh` installs dependencies and records
the DuckDB VSS fallback. The `task` command is still missing, so Taskfile
recipes cannot run. Test dependencies load after `uv pip install -e '.[test]'`.

## Lint, type checks, and spec tests
```text
task check
```
Result: `task` command not found.

## Unit tests
```text
uv run pytest
```
Result: `9 failed, 443 passed, 8 skipped, 117 deselected, 1 xpassed`.
Failing tests:
- `tests/unit/test_cli_backup_extra.py::test_backup_restore_error`
- `tests/unit/test_download_duckdb_extensions.py::test_download_extension_network_fallback`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_setup_with_default_path`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_initialize_schema_version`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_get_schema_version`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_get_schema_version_no_version`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_close`
- `tests/unit/test_main_backup_commands.py::test_backup_restore_command`
- `tests/unit/test_main_backup_commands.py::test_backup_restore_error`

## Integration tests
```text
Integration tests did not run; unit tests failed.
```

## Behavior tests
```text
Behavior tests did not run; unit tests failed.
```

## Coverage
`task verify` cannot run without `task`, so coverage remains unavailable. The
previous baseline was **14%**, below the required 90% threshold.
