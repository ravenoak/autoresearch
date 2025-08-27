# Status

As of **August 27, 2025**, the environment includes the `task` CLI. Running
`task check` executes linting, type checks, spec tests, and the unit subset.
The command reports **9 failed, 336 passed, 1 skipped, 24 deselected, 1 xpassed**
unit tests in about two minutes. Required packages, including `pdfminer.six`,
are present.

## Lint, type checks, and spec tests
`task check` runs successfully until unit test failures occur. `flake8` and
`mypy` pass without errors.

## Unit tests
`task check` reports failures in the following tests:
- `tests/unit/test_cli_backup_extra.py::test_backup_restore_error`
- `tests/unit/test_download_duckdb_extensions.py::test_download_extension_network_fallback`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_setup_with_default_path`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_initialize_schema_version`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_get_schema_version`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_get_schema_version_no_version`
- `tests/unit/test_duckdb_storage_backend.py::TestDuckDBStorageBackend::test_close`
- `tests/unit/test_main_backup_commands.py::test_backup_restore_command`
- `tests/unit/test_main_backup_commands.py::test_backup_restore_error`

## Targeted tests
`task verify` fails during collection with an `ImportError` from a circular
import between `distributed.executors` and `orchestration.state`.

## Integration tests
```text
Integration tests did not run; targeted tests failing.
```

## Behavior tests
```text
Behavior tests did not run; targeted tests failing.
```

## Coverage
Coverage remains unavailable because targeted tests failed. The previous
baseline was **14%**, below the required 90% threshold.
