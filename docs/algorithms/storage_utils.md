# Storage Utilities

## Overview
`storage_utils` provides helpers for storage backends.

## Algorithm
`initialize_schema_version_without_fetchone` reads the metadata table and
inserts version `1` when absent, even on cursors lacking `fetchone`.

## Proof sketch
Every path either finds a value or performs a single insert, so the
metadata contains at most one schema version row.

## Simulation
`tests/integration/test_storage_schema.py` exercises initialization on a
mock connection without `fetchone`.

## References
- [code](../../src/autoresearch/storage_utils.py)
- [spec](../specs/storage-utils.md)
- [tests](../../tests/integration/test_storage_schema.py)

## Related Issues
- [Fix storage schema and eviction tests][issue]

[issue]: ../../issues/archive/fix-storage-schema-and-eviction-tests.md
