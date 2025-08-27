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

## Formal proofs

### Schema idempotency

**Theorem.** Repeated calls to `initialize_storage` yield an identical set of
tables.

**Proof.** Let `R` be the required table set. Each call issues
`CREATE TABLE IF NOT EXISTS` for every element of `R`. The command is
idempotent: if a table exists, execution is a no-op. No other schema mutations
occur. Therefore, after any number of invocations the table set equals `R` and
ordering differences are irrelevant. The
[targeted test][schema-test] and [deterministic test][evict-test] both observe
equal table lists across runs. ∎

### Eviction correctness under concurrent writers

**Theorem.** `_enforce_ram_budget` preserves the invariant `U ≤ B(1 − δ)` under
concurrent writes, where `U` is usage, `B` the budget, and `δ` the safety
margin.

**Proof.** The function acquires a lock before measuring `U`. If `U > B`, it
removes nodes according to the configured policy until `U ≤ B(1 − δ)`. Because
the lock serializes eviction, no two writers can evict based on stale
information. Every invocation reduces or maintains `U`; thus, after all
threads finish, the invariant holds. The
[simulation][evict-sim] and [deterministic test][evict-test] confirm the final
graph is empty when `U` is forced above `B`. ∎

## DuckDB fallback benchmark

The benchmark in [duckdb-bench] shows that persistence triggers eviction when
the RAM budget is exceeded, ensuring deterministic resource bounds.

[evict-sim]: ../../scripts/storage_eviction_sim.py
[duckdb-bench]: ../../tests/integration/test_storage_duckdb_fallback.py
[schema-test]: ../../tests/targeted/test_storage_eviction.py
[evict-test]: ../../tests/targeted/test_storage_eviction.py

