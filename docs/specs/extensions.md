# Extensions

## Overview

DuckDB extension management module that loads and verifies extensions such
as the vector search system (VSS).

## Algorithms

1. ``VSSExtensionLoader.load_extension`` tries the configured path then
   downloads from DuckDB.
2. ``verify_extension`` queries ``duckdb_extensions()`` to confirm the module
   is active.
3. When ``AUTORESEARCH_STRICT_EXTENSIONS=true``, failures raise
   ``StorageError``.

## Invariants

- Preserve documented state across operations.
- Verification runs after every load attempt.

## Proof Sketch

Core routines enforce invariants by validating inputs and state and by
ensuring strict mode stops on failures.

## Simulation Expectations

Unit tests cover nominal and edge cases for these routines.

## Traceability


- Modules
  - [src/autoresearch/extensions.py][m1]
- Tests
  - [tests/unit/test_duckdb_storage_backend.py][t1]
  - [tests/unit/test_vss_extension_loader.py][t2]

[m1]: ../../src/autoresearch/extensions.py
[t1]: ../../tests/unit/test_duckdb_storage_backend.py
[t2]: ../../tests/unit/test_vss_extension_loader.py
