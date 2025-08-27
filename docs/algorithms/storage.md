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

### Proof

- `CREATE TABLE IF NOT EXISTS` guarantees that an existing table remains
  untouched. DuckDB documents this behaviour in its [SQL
  reference](https://duckdb.org/docs/sql/statements/create_table.html).
- The `setup` helper issues that statement for each table, so repeated
  invocations cannot modify the schema.
- The above code sample runs the setup twice and compares table listings,
  providing a constructive witness that the schema is unchanged.

## Concurrent eviction

Eviction maintains the RAM budget even when multiple writers persist claims
simultaneously. The [simulation][evict-sim] spawns threads that insert claims
while memory usage is forced above the budget. After all threads finish the
in-memory graph is empty, proving the policy is thread safe.

### Proof

- Every `persist_claim` call ends with `_enforce_ram_budget`, which checks
  current memory use against `ram_budget_mb`.
- The simulation patches the memory check so each write appears to exceed the
  budget and runs several threads that insert claims.
- After the threads join the NetworkX graph reports zero nodes, which the
  [targeted test][evict-test] asserts, confirming evicted state under
  concurrency.

## DuckDB fallback benchmark

The benchmark in [duckdb-bench] shows that persistence triggers eviction when
 the RAM budget is exceeded, ensuring deterministic resource bounds.

[evict-sim]: ../../scripts/storage_eviction_sim.py
[evict-test]: ../../tests/targeted/test_storage_eviction.py
[duckdb-bench]: ../../tests/integration/test_storage_duckdb_fallback.py
