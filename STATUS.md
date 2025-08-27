# Status

As of **August 27, 2025**, running `scripts/codex_setup.sh` then
`.venv/bin/task install` provisions dependencies and exposes the `task`
command. `task check` executes linting and type checks, but nine unit tests
fail and the run ends early. `task verify` aborts during collection because the
`pdfminer` package is missing.

## Lint, type checks, and spec tests
```text
task check
```
Result: lint and type checks passed; unit tests failed before completion.

## Unit tests
`task check` reported failures in the following tests:
- `tests/unit/test_cli_backup_extra.py::test_backup_restore_error`
- `tests/unit/test_download_duckdb_extensions.py::`
  `test_download_extension_network_fallback`
- `tests/unit/test_duckdb_storage_backend.py::`
  `TestDuckDBStorageBackend::test_setup_with_default_path`
- `tests/unit/test_duckdb_storage_backend.py::`
  `TestDuckDBStorageBackend::test_initialize_schema_version`
- `tests/unit/test_duckdb_storage_backend.py::`
  `TestDuckDBStorageBackend::test_get_schema_version`
- `tests/unit/test_duckdb_storage_backend.py::`
  `TestDuckDBStorageBackend::test_get_schema_version_no_version`
- `tests/unit/test_duckdb_storage_backend.py::`
  `TestDuckDBStorageBackend::test_close`
- `tests/unit/test_main_backup_commands.py::test_backup_restore_command`
- `tests/unit/test_main_backup_commands.py::test_backup_restore_error`

## Targeted tests
```text
task verify
```
Result: collection errors (`ModuleNotFoundError: No module named 'pdfminer'`).

## Integration tests
```text
Integration tests did not run; unit tests failing.
```

## Behavior tests
```text
Behavior tests did not run; unit tests failing.
```

## Coverage
Coverage remains unavailable because tests failed. The previous baseline was
**14%**, below the required 90% threshold.
