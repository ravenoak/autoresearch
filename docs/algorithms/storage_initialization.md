# Storage Initialization

## Overview

Storage initialization prepares DuckDB and its vector extension so that
callers can persist and query graph data. This spec covers extension
downloads and table creation routines.

## Algorithms

- **Extension download:** `scripts/download_duckdb_extensions.py` downloads
  required extensions. It retries network failures, then loads a cached copy
  recorded in `.env.offline`. If no copy exists, it creates an empty stub so
  subsequent runs can still proceed.
- **Table creation:** `initialize_storage` opens a DuckDB connection and
  invokes `_create_tables` on the backend. The helper issues `CREATE TABLE IF
  NOT EXISTS` for `nodes`, `edges`, `embeddings`, and `metadata` so that the
  schema is present on first use.

## Invariants

- After running the extension algorithm, a real extension or zero-byte stub
  exists at the target path even when downloads fail.
- When the vector extension is requested but cannot be loaded, the storage
  backend sets `has_vss` to `False` and still initializes the schema.
- After calling `initialize_storage`, all required tables exist and repeated
  calls leave the schema unchanged.

## Proof Sketch

- *Extension presence.* The download routine checks the cache after network
  retries. If no copy exists, it writes an empty stub and records its location
  in `.env.offline`. Therefore a file always exists, satisfying the first
  invariant.
- *Missing extension tolerance.* During `setup` the backend loads the vector
  extension. On failure it clears `has_vss` and still invokes `_create_tables`.
  As table creation does not depend on `has_vss`, initialization succeeds,
  establishing the second invariant.
- *Table idempotence.* `_create_tables` executes `CREATE TABLE IF NOT EXISTS`
  for `nodes`, `edges`, `embeddings`, and `metadata`. Idempotence of this
  command guarantees that repeated calls yield the same schema, proving the
  final invariant.

## Simulation Expectations

- **Extension failure pseudocode**

  ```text
  simulate_load_extension_failure():
      patch VSSExtensionLoader.load_extension -> raise duckdb.Error
      ctx = initialize_storage(path)
      assert ctx.db_backend.has_vss() is False
      assert required_tables_exist(ctx.db_backend)
  ```

- **Table creation pseudocode**

  ```text
  simulate_table_creation():
      path = temporary_file()
      ctx = initialize_storage(path)
      for table in ["nodes", "edges", "embeddings", "metadata"]:
          ctx.db_backend._conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
      ctx.teardown(remove_db=True)
  ```

- Network failure simulations live in
  [`download_duckdb_extensions` tests][download].
- Table creation and extension fallback are validated in
  `tests/unit/test_storage_persistence.py` and
  `tests/unit/test_duckdb_storage_backend.py`.

## Traceability

- Extension handling: [scripts/download_duckdb_extensions.py][dde]
- Storage setup: [src/autoresearch/storage.py][storage]
- Backend logic: [src/autoresearch/storage_backends.py][backend]
- Tests: [tests/unit/test_storage_persistence.py][persistence],
  [tests/unit/test_duckdb_storage_backend.py][backend-test]

[dde]: ../../scripts/download_duckdb_extensions.py
[storage]: ../../src/autoresearch/storage.py
[backend]: ../../src/autoresearch/storage_backends.py
[persistence]: ../../tests/unit/test_storage_persistence.py
[backend-test]: ../../tests/unit/test_duckdb_storage_backend.py
[download]: ../../tests/unit/test_download_duckdb_extensions.py
