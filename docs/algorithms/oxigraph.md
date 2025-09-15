# OxiGraph Schema Idempotency and Persistence

Repeated initialization of the OxiGraph backend leaves the schema unchanged and
keeps data across restarts until the store is explicitly removed.

## Simulation

`scripts/oxigraph_persistence_sim.py` performs several setup cycles with a
sentinel triple. The first cycle inserts the triple, later cycles verify its
presence, and the run ends by deleting the store.

Run:

`uv run python scripts/oxigraph_persistence_sim.py --runs 3 --force`

The command prints `completed 3 cycles` and leaves no residual directory,
demonstrating deterministic creation and teardown.

## Proof

OxiGraph uses file backed storage. When the store path exists, opening the store
without the create flag reuses the prior schema. Because each cycle observes the
sentinel triple, schema creation is idempotent and persistence holds until the
directory is removed. See [OxiGraph](https://github.com/oxigraph/oxigraph) for
backend details.

