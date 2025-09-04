# DuckDB VSS Fallback

When network access is limited, Autoresearch falls back to a stubbed vector
search extension for DuckDB. The stub allows tests to run while
disabling vector search features.

## Stub mechanism

- [`download_duckdb_extensions.py`][dde] installs the VSS extension.
- On repeated failures it creates an empty file in `extensions/vss/` and warns
  that the stub is in use.
- [`setup.sh`][setup] logs when the stub is selected and records its
  location for reuse.

## Environment variable usage

- The stub path is stored in `.env.offline` under `VECTOR_EXTENSION_PATH`.
- Later runs load this file so `download_duckdb_extensions.py` can copy the
  recorded extension instead of downloading it again.
- Update or create `.env.offline` with:

```
VECTOR_EXTENSION_PATH=/path/to/vss.duckdb_extension
```

- The unit test [`test_download_duckdb_extensions.py`][test] demonstrates this
  fallback.

[dde]: ../scripts/download_duckdb_extensions.py
[setup]: ../scripts/setup.sh
[test]: ../tests/unit/test_download_duckdb_extensions.py
