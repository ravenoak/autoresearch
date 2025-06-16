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

### Linux (x86_64)
- Full support for DuckDB and VSS extension
- Extension path: `./extensions/vss/linux/vss.duckdb_extension`

### macOS (Intel)
- Full support for DuckDB and VSS extension
- Extension path: `./extensions/vss/osx/vss.duckdb_extension`

### macOS (ARM64/M1/M2)
- Full support for DuckDB and VSS extension
- Extension path: `./extensions/vss/osx_arm64/vss.duckdb_extension`

### Windows
- Limited testing, but should work
- Extension path: `./extensions/vss/windows/vss.duckdb_extension`

## Offline Usage

For offline environments, the VSS extension can be pre-downloaded using the provided script:

```bash
python scripts/download_duckdb_extensions.py --output-dir ./extensions
```

This will download the appropriate VSS extension for your platform and store it in the specified directory.

## Troubleshooting

If you encounter issues with the VSS extension:

1. Ensure you have the correct version of DuckDB installed
2. Check that the VSS extension is available in the expected location
3. Set the `vector_extension_path` in your configuration to point to the extension file
4. For offline environments, use the `.env.offline` configuration

If the extension fails to load, the system will log an error but continue to function without vector search capabilities.