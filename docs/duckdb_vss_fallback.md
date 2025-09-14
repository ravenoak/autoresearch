# DuckDB VSS Fallback

When network access is limited, Autoresearch falls back to a stubbed vector
search extension for DuckDB. The stub allows tests to run while
disabling vector search features.

## Loading order

`VSSExtensionLoader.load_extension` tries multiple strategies:

1. Load a user provided path from `storage.vector_extension_path` or
   `.env.offline`'s `VECTOR_EXTENSION_PATH`.
2. Install and load the official `vss` extension from DuckDB's repository.
3. Load the binary shipped with the `duckdb_extension_vss` Python package.
4. Fall back to the stub in `extensions/vss/` when all else fails.
5. If the stub binary is missing, a temporary `vss_stub` table marks the
   extension as loaded so offline tests can proceed.

The loader only raises :class:`StorageError` when
`AUTORESEARCH_STRICT_EXTENSIONS=true`.

## Stub mechanism

- [`download_duckdb_extensions.py`][dde] installs the VSS extension.
- On repeated failures it creates an empty file in `extensions/vss/` and warns
  that the stub is in use.
- [`setup.sh`][setup] logs when the stub is selected and records its
  location for reuse.

## Environment variable usage

- The stub path is stored in `.env.offline` under `VECTOR_EXTENSION_PATH`.
- Later runs load this file so `download_duckdb_extensions.py` or
  `VSSExtensionLoader` can reuse the recorded extension instead of downloading
  it again.
- Update or create `.env.offline` with:

```
VECTOR_EXTENSION_PATH=/path/to/vss.duckdb_extension
ENABLE_ONLINE_EXTENSION_INSTALL=false
```

- The unit test [`test_download_duckdb_extensions.py`][test] demonstrates this
  fallback.

## Testing the stub

Run the integration test to confirm the stub activates when the VSS extension
is missing:

```bash
uv run pytest \
  tests/integration/test_storage_duckdb_fallback.py::test_duckdb_vss_fallback \
  -q
```

The test imports `pytest-benchmark`; install it if the module is skipped.


[dde]: ../scripts/download_duckdb_extensions.py
[setup]: ../scripts/setup.sh
[test]: ../tests/unit/test_download_duckdb_extensions.py
