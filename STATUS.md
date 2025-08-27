# Status

As of **August 27, 2025**, the environment lacks the `task` CLI. After
`uv sync --all-extras`, running `uv run pytest` exercises the suite with nine
failing tests and 429 passing tests. Required packages, including
`pdfminer.six`, are present.

## Lint, type checks, and spec tests
`task check` could not run because the `task` command is unavailable.

## Unit tests
`uv run pytest` reported failures in the following tests:
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
`task verify` could not run because the `task` command is unavailable.

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
