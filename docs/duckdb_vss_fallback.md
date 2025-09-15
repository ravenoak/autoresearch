# DuckDB VSS Fallback

When network access is limited, Autoresearch falls back to a stubbed vector
search extension for DuckDB. The stub allows tests to run while
disabling vector search features.

## Loading order

`VSSExtensionLoader.load_extension` tries multiple strategies:

1. Load a user provided path from `storage.vector_extension_path` or
   `.env.offline`'s `VECTOR_EXTENSION_PATH`.
2. Install and load the official `vss` extension from DuckDB's repository.
   Network failures fall through to the remaining steps.
3. Load the binary shipped with the `duckdb_extension_vss` Python package.
4. Fall back to the stub in `extensions/vss/` when all else fails.
5. If the stub binary is missing, a temporary `vss_stub` table marks the
   extension as loaded so offline tests can proceed.

The loader only raises :class:`StorageError` when
`AUTORESEARCH_STRICT_EXTENSIONS=true`.

## Stub mechanism

- `download_duckdb_extensions.py` installs the VSS extension.
- If `VECTOR_EXTENSION_PATH` is present in `.env.offline` the script copies
  that file into the requested output directory and updates the environment
  variable to point at the copy. It compares the cached source and
  destination with `os.path.samefile` and skips the copy when they already
  point to the same file, avoiding a `SameFileError`.
- When no path is provided it creates an empty file in `extensions/vss/`,
  sets `VECTOR_EXTENSION_PATH` to the stub and warns that the stub is in
  use. The stub is opened with ``open(path, "wb")`` so repeated runs
  truncate the file back to zero bytes if earlier attempts wrote data.
- `setup.sh` logs when the stub is selected and records its location for
  reuse.

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

- The unit test `test_download_duckdb_extensions.py` demonstrates this
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


