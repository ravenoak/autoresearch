# Storage Schema Idempotency and Eviction

Autoresearch guarantees that repeated storage initialization yields the same
schema and that eviction policies remain effective under concurrent access.

## Schema bootstrapping

`initialize_storage` runs setup and verifies that the core DuckDB tables
exist. If a database starts empty—such as when using `:memory:`—the helper
creates the `nodes`, `edges`, `embeddings`, and `metadata` tables so callers
can assume the schema is present.

## Schema idempotency

DuckDB tables are created with `CREATE TABLE IF NOT EXISTS`, making setup
operations repeatable. The snippet shows two calls that leave the schema
unchanged:

```python
from autoresearch.storage import StorageContext, StorageManager, StorageState

ctx, st = StorageContext(), StorageState()
StorageManager.setup(db_path=":memory:", context=ctx, state=st)
first = ctx.db_backend._conn.execute("show tables").fetchall()
StorageManager.setup(db_path=":memory:", context=ctx, state=st)
second = ctx.db_backend._conn.execute("show tables").fetchall()
assert first == second
```

## Deterministic setup and teardown

`DuckDBStorageBackend.setup` now retains the database path, even for
`:memory:`, and initializes the schema version with a single `fetchone` query.
`close` always releases the connection and clears the path whether or not a
pool is in use, ensuring each run starts from a clean slate.

## Concurrent eviction

Eviction maintains the RAM budget even when multiple writers persist claims
simultaneously. The [simulation][evict-sim] spawns threads that insert claims
while memory usage is forced above the budget. After all threads finish the
in-memory graph is empty, proving the policy is thread safe.

## DuckDB fallback benchmark

The benchmark in [duckdb-bench] shows that persistence triggers eviction when
 the RAM budget is exceeded, ensuring deterministic resource bounds.

[evict-sim]: ../../tests/integration/test_storage_eviction.py
[duckdb-bench]: ../../tests/integration/test_storage_duckdb_fallback.py
