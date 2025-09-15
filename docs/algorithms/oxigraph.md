# OxiGraph Schema Idempotency and Durability

Repeated initialization of the OxiGraph backend leaves the schema unchanged and
keeps data across restarts until the store is explicitly removed.

## Proof

OxiGraph uses file backed storage. The `open` call accepts a `create` flag. When
a new path is provided with `create=True`, the schema is written to disk once.
Later openings omit the flag, so the call reuses the existing files without
altering the schema. A sentinel triple inserted in the first run persists across
restarts, showing that no second initialization occurs and that data remains on
disk until the directory is deleted. Therefore schema creation is idempotent and
the store is durable.

## Simulation

`scripts/oxigraph_persistence_sim.py` performs several setup cycles with a
sentinel triple. The first cycle inserts the triple, later cycles verify its
presence, and the run ends by deleting the store.

Run:

`uv run python scripts/oxigraph_persistence_sim.py --runs 3 --force`

The command prints `completed 3 cycles` and leaves no residual directory,
demonstrating deterministic creation and teardown.

