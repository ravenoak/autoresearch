# Extensions

## Overview

DuckDB extension management module that loads and verifies extensions such
as the vector search system (VSS).

## Algorithms

1. ``VSSExtensionLoader.load_extension`` attempts, in order:
   1. ``storage.vector_extension_path``
   2. ``VECTOR_EXTENSION_PATH`` from the environment or ``.env.offline``
   3. ``duckdb_extension_vss`` package
   4. repository stub ``extensions/vss/vss.duckdb_extension``
   5. creation of a ``vss_stub`` marker table
2. ``verify_extension`` queries ``duckdb_extensions()`` or checks the marker
   table to confirm activation.
3. When ``AUTORESEARCH_STRICT_EXTENSIONS=true``, failures raise
   ``StorageError``.
4. ``scripts/download_duckdb_extensions.py`` writes
   ``VECTOR_EXTENSION_PATH`` to ``.env.offline`` and creates a stub when
   downloads fail so offline runs succeed.

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
