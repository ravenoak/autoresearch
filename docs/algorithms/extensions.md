# Extensions

Manage DuckDB extensions, especially the VSS module.

## VSS loading
- `VSSExtensionLoader.load_extension` tries a configured path then downloads.
- `verify_extension` queries `duckdb_extensions()` to confirm status.

## Strict mode
- When `AUTORESEARCH_STRICT_EXTENSIONS=true`, failures raise `StorageError`.

## References
- [`extensions.py`](../../src/autoresearch/extensions.py)
- [../specs/extensions.md](../specs/extensions.md)

## Simulation

Automated tests confirm extensions behavior.

- [Spec](../specs/extensions.md)
- [Tests](../../tests/integration/test_vector_search_params.py)
