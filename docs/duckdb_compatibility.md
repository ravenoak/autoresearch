# DuckDB and VSS Extension Compatibility

This document provides information about the compatibility between DuckDB versions and the VSS extension across different platforms.

## Supported DuckDB Versions

The autoresearch project uses DuckDB for relational storage and vector search. The following DuckDB versions are supported:

- **Minimum version**: 1.2.2
- **Maximum version**: < 2.0.0

## VSS Extension Compatibility

The VSS extension (formerly known as "vector") is used for vector similarity search. It's compatible with the following DuckDB versions:

| DuckDB Version | VSS Extension Version | Notes |
|----------------|------------------------|-------|
| 1.2.x          | Latest                 | Fully compatible |
| 1.3.x          | Latest                 | Fully compatible |

## Platform-Specific Considerations

The VSS extension is available for the following platforms:

### Linux (x86_64/AMD64)
- Full support for DuckDB and VSS extension
- Platform identifier: `linux_amd64`
- Extension path: `./extensions/vss/vss.duckdb_extension`

### Linux (ARM64/AArch64)
- Full support for DuckDB and VSS extension
- Platform identifier: `linux_arm64`
- Extension path: `./extensions/vss/vss.duckdb_extension`

### macOS (Intel)
- Full support for DuckDB and VSS extension
- Platform identifier: `osx_amd64`
- Extension path: `./extensions/vss/vss.duckdb_extension`

### macOS (ARM64/M1/M2)
- Full support for DuckDB and VSS extension
- Platform identifier: `osx_arm64`
- Extension path: `./extensions/vss/vss.duckdb_extension`

### Windows (x86_64/AMD64)
- Limited testing, but should work
- Platform identifier: `windows_amd64`
- Extension path: `./extensions/vss/vss.duckdb_extension`

Note: The download script automatically detects your platform and downloads the appropriate extension. The extension file is placed directly in the `./extensions/vss/` directory without platform-specific subdirectories.

## Offline Usage

For offline environments, the VSS extension can be pre-downloaded using the provided script:

```bash
# Download for the current platform (auto-detected)
python scripts/download_duckdb_extensions.py --output-dir ./extensions

# Download for a specific platform
python scripts/download_duckdb_extensions.py --output-dir ./extensions --platform linux_amd64

# Download multiple extensions
python scripts/download_duckdb_extensions.py --output-dir ./extensions --extensions vss,json
```

If you already have the `.duckdb_extension` file available, copy it under
`extensions/vss/` before running `scripts/setup.sh`. The setup script will
detect the file and skip the download step, making offline installation
easier.

This will download the appropriate VSS extension for the specified platform and
store it in the specified directory. If the download fails, the script logs a
warning and exits so the application can continue without the extension. The
script will output the exact path to use in your configuration file.

### Configuration for Offline Use

After downloading the extension, update your `autoresearch.toml` file with the path to the extension file:

```toml
[storage.duckdb]
vector_extension = true
vector_extension_path = "./extensions/vss/vss.duckdb_extension"
```

Note that the `vector_extension_path` must point to the actual `.duckdb_extension` file, not just the directory.
When running on Windows, use forward slashes in the path (e.g. `C:/path/to/vss.duckdb_extension`) so DuckDB can load the extension correctly.

### Refreshing the Vector Index

When new embeddings are inserted, refresh the HNSW index so that vector search
includes them:

```python
from autoresearch.storage import StorageManager

StorageManager.refresh_vector_index()
```

### Alternative: Using the Python Package

As an alternative to manually downloading the extension, you can use the `duckdb-extension-vss` Python package, which is included as a dependency in the project. This package automatically provides the correct VSS extension for your platform.

## Troubleshooting

If you encounter issues with the VSS extension:

1. Ensure you have the correct version of DuckDB installed
2. Check that the VSS extension is available in the expected location
3. Set the `vector_extension_path` in your configuration to point to the extension file
4. For offline environments, use the `.env.offline` configuration

If the extension fails to load, Autoresearch logs a warning and runs without
vector search. Calls to ``StorageManager.vector_search`` then return an empty
list.

