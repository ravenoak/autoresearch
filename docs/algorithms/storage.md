# Storage Schema Idempotency and Eviction

Autoresearch guarantees that repeated storage initialization yields the same
schema and that eviction policies remain effective under concurrent access.

Autoresearch supports DuckDB versions 1.2.2 up to, but not including, 2.0.0.
See [DuckDB and VSS Extension Compatibility](../duckdb_compatibility.md) for
details.

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

## Proof sketches

### Idempotent schema initialization

1. `initialize_storage` wraps each table creation in `CREATE TABLE IF NOT
   EXISTS`.
2. Repeated setup runs `SHOW TABLES` and creates only the missing entries.
3. Table definitions are deterministic, so every run yields the same schema.
4. The [targeted test][schema-test] calls the helper twice on an in-memory
   database and observes identical table lists.

### RAM-budget eviction

1. `_enforce_ram_budget` compares the measured usage `U` against the budget
   `B`.
2. When `U > B`, nodes are removed until usage falls below `B(1 -
   safety_margin)`.
3. Eviction occurs within a lock, so concurrent writers cannot race.
4. The [simulation][evict-sim] forces `U` above `B`; after all threads finish
   the graph is empty, proving the budget is upheld.

## DuckDB fallback benchmark

The benchmark in [duckdb-bench] shows that persistence triggers eviction when
the RAM budget is exceeded, ensuring deterministic resource bounds.

[evict-sim]: ../../scripts/storage_eviction_sim.py
[duckdb-bench]: ../../tests/integration/test_storage_duckdb_fallback.py
[schema-test]: ../../tests/targeted/test_storage_eviction.py
