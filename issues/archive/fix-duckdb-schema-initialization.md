# Fix DuckDB schema initialization

## Context
Integration and behavior tests fail because `DuckDBStorageBackend._initialize_schema_version`
uses `fetchone` on a `DuckDBPyConnection`, raising `AttributeError` and preventing
table creation.

## Dependencies
- None

## Acceptance Criteria
- Use a `DuckDBPyCursor` or `fetchall` to check for the schema version without
  triggering `AttributeError`.
- Integration tests complete without `StorageError`.
- Behavior tests involving storage pass.
- Document the fix in `docs/algorithms/storage.md`.

## Status
Archived
