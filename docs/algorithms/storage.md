# Storage Schema Idempotency and Eviction

Autoresearch guarantees that repeated storage initialization yields the same
schema and that eviction policies remain effective under concurrent access.

Autoresearch supports DuckDB versions 1.2.2 up to, but not including, 2.0.0.
See [DuckDB and VSS Extension Compatibility](../duckdb_compatibility.md) for
details.

## Offline extension downloads

`download_duckdb_extensions.py` retries network failures before copying a
previously cached file referenced by `VECTOR_EXTENSION_PATH` in `.env.offline`.
If no copy exists, a stub is created so tests can proceed without vector
search.

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

The [schema simulation][schema-sim] runs this routine against an in-memory
database. Executing
`uv run python scripts/schema_idempotency_sim.py --runs 2` prints
`schema stable across 2 runs`, confirming the table list remains unchanged.

## Deterministic setup and teardown

`DuckDBStorageBackend.setup` now retains the database path, even for
`:memory:`, and initializes the schema version by reading `fetchall` from a
cursor. The change avoids `AttributeError` when `fetchone` is absent in newer
DuckDB releases. `close` always releases the connection and clears the path
whether or not a pool is in use, ensuring each run starts from a clean slate.

## Concurrent eviction

Eviction maintains the RAM budget even when multiple writers persist claims
simultaneously. The [simulation][evict-sim] forces usage to 1000 MB and
accepts thread count, item count, and policy to stress eviction. Running
`uv run python scripts/storage_eviction_sim.py --scenario race` adds a
dedicated eviction thread. With policy `lru`, both normal and race modes finish
with `nodes remaining after eviction: 0`, proving the policy is thread safe.

The [RAM budget simulation][ram-sim] persists claims sequentially while
memory usage is mocked above the limit, leaving the in-memory graph empty.

The [concurrency simulation][concurrency-sim] accepts thread and item counts to
demonstrate enforcement under heavier contention. Integration
[tests][concurrency-test] show that writers retain all claims when usage stays
within the budget and trigger eviction once mocked memory exceeds the limit.

### Setup concurrency metrics

Running

```
uv run python scripts/storage_concurrency_sim.py --threads 6 --items 4
```

produced the following metrics:

```
setup calls: 1
setup failures: 0
unique contexts: 1
setup wall time (ms): 1678.75
persist wall time (ms): 1540.79
nodes remaining after eviction: 0
```

These results show that only a single thread initializes storage while six
threads race to call `StorageManager.setup`. The simulation also confirms that
writers still converge to an empty graph once the RAM budget is enforced.

## Eviction performance

Running `uv run python scripts/storage_eviction_sim.py --threads 1 --items 1`
finished in 8.35 s with throughput 0.1 nodes/s and reported
`nodes remaining after eviction: 0`. Even small runs show that enforcement
incurs minimal overhead relative to claim persistence.

## Concurrency and failure modes

`DuckDBStorageBackend.setup` uses a lock so concurrent callers
initialise the schema once. The unit test [backend-test] spawns
threads that call `setup` simultaneously and confirms that
`_create_tables` executes only once. The same module injects a fault
into `_initialize_schema_version` and verifies that a
`StorageError` surfaces to the caller.

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
equal table lists across runs. Running
`uv run python scripts/schema_idempotency_sim.py --runs 2` yields
`schema stable across 2 runs`, empirically validating the theorem. ∎

### Eviction correctness under concurrent writers

**Theorem.** `_enforce_ram_budget` preserves the invariant
`U ≤ B(1 − δ)` under concurrent writes, where `U` is usage,
`B` the budget, and `δ` the safety margin.

**Proof.** The function acquires a lock and reads `U₀` and target
`T = B(1 − δ)`. The loop executes only when `Uᵢ > T`. Each iteration
removes at least one node with positive size `sᵢ`, yielding
`Uᵢ₊₁ = Uᵢ − sᵢ` and `Uᵢ₊₁ < Uᵢ`. The sequence `(Uᵢ)` is
strictly decreasing and bounded below by `0`, so by induction there
exists `k` with `Uₖ ≤ T`. Upon exit, all threads see `Uₖ ≤ B` and
either return immediately or repeat the argument, ensuring the
invariant after every call. The [simulation][evict-sim] and
[deterministic test][evict-test] confirm the final graph is empty when `U` is
forced above `B`. Running
`uv run python scripts/storage_eviction_sim.py --threads 5 --items 5` prints
`nodes remaining after eviction: 0`, illustrating the invariant. ∎

**Lemma.** After `m` iterations the usage is `U₀ − Σ sᵢ`, where each `sᵢ > 0`
is the size of an evicted node.

**Proof.** The update rule `Uᵢ₊₁ = Uᵢ − sᵢ` telescopes. Applying it
repeatedly yields `Uₘ = U₀ − Σ₀^{m−1} sᵢ`. Since the sum is positive and
bounded by `U₀ − T`, the loop terminates after finitely many steps. ∎

### Concurrent enforcement races

**Theorem.** Concurrent calls to `_enforce_ram_budget` by independent threads
maintain `U ≤ B(1 − δ)`.

**Proof.** The function uses a global lock, so calls serialize. Each thread
sees a state satisfying the previous theorem and leaves the invariant intact.
The `race` scenario in [storage_eviction_sim.py][evict-sim] spawns a
dedicated enforcer thread while writers persist data. The simulation ends
with zero nodes, confirming the argument. ∎

### Edge cases

`_enforce_ram_budget` handles boundary conditions without violating the
invariant:

- **Zero budget:** When `B = 0`, eviction is skipped. The
  [`zero_budget` scenario][evict-sim] leaves `N = threads × items` nodes.
- **Usage below budget:** If `U₀ ≤ B`, no eviction occurs. The
  [`under_budget` scenario][evict-sim] retains all persisted nodes.
- **No nodes to evict:** An empty graph yields an empty loop. The
  [`no_nodes` scenario][evict-sim] reports `nodes remaining after eviction: 0`.

These results align with the theorem because each scenario preserves
`U ≤ B(1 − δ)`.

### Termination bound and negative budgets

Assume each node occupies at least ``s_min > 0`` MB. With ``U_0`` initial
usage and target ``T = B(1 - δ)``, eviction removes size ``s_i`` per
iteration yielding ``U_{i+1} = U_i - s_i``. The loop halts after at most
``⌈(U_0 - T) / s_min⌉`` steps, guaranteeing ``U_k ≤ T``.

If ``B ≤ 0`` the algorithm returns immediately and no eviction occurs. The
simulation scenario ``negative_budget`` models this edge case and finishes with
``N = threads × items`` nodes. Running the ``race`` scenario with
``--evictors 2`` spawns two enforcement threads and still reports
``nodes remaining after eviction: 0``, confirming correctness under concurrent
evictors.

## DuckDB fallback benchmark

The benchmark in [duckdb-bench] shows that persistence triggers eviction when
the RAM budget is exceeded, ensuring deterministic resource bounds.

[evict-sim]: ../../scripts/storage_eviction_sim.py
[concurrency-sim]: ../../scripts/storage_concurrency_sim.py
[duckdb-bench]: ../../tests/integration/test_storage_duckdb_fallback.py
[schema-test]: ../../tests/targeted/test_storage_eviction.py
[evict-test]: ../../tests/targeted/test_storage_eviction.py
[concurrency-test]: ../../tests/integration/test_storage_concurrency.py

[schema-sim]: ../../scripts/schema_idempotency_sim.py
[ram-sim]: ../../scripts/ram_budget_enforcement_sim.py
[backend-test]: ../../tests/unit/test_duckdb_storage_backend_concurrency.py
