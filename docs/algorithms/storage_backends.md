# Storage Backends

Idempotent schema creation prevents accidental data loss. The DuckDB backend's
`setup` function checks whether a connection already exists and returns
immediately if so, avoiding repeated data definition. The early-return logic is
implemented in [storage_backends.py](../../src/autoresearch/storage_backends.py)
lines 75-77.

Proof. Let `S` be the state of the schema after one call to `setup`. On a
second call, the function exits before any table creation, leaving the database
unchanged. Therefore `setup(setup(db)) = setup(db)`, establishing idempotence.
The simulation script
[schema_idempotency_sim.py](../../scripts/schema_idempotency_sim.py) runs the
initialization several times and confirms identical table listings.

This guarantee allows multiple components to invoke setup safely without
introducing divergent schemas.
