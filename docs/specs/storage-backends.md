# Storage Backends

## Overview

Storage backend implementations for the autoresearch project.

## Algorithms

- Implement core behaviors described above.

## Invariants

- Preserve documented state across operations.

## Proof Sketch

Core routines enforce invariants by validating inputs and state.

## Simulation Expectations

Unit tests cover nominal and edge cases for these routines.

## OxiGraph Backend

### Proof Sketch

- Setup opens an ``OxigraphStore`` at the requested path. When the directory
  exists, ``rdflib.Graph.open`` reuses it; otherwise ``create=True`` initializes
  a new store.
- Teardown removes the directory with ``shutil.rmtree(..., ignore_errors=True)``
  so repeated calls leave no residue.

### Simulation

Run [scripts/oxigraph_backend_sim.py][s1] to exercise repeated setup and
teardown.

### Setup

- Install `oxrdflib` with `uv pip install oxrdflib` to enable the OxiGraph
  RDF store.
- Verify the driver is discoverable with
  `uv run python -c "import oxrdflib"`.
- Set `storage.rdf_backend` to `oxigraph` and provide `storage.rdf_path`.
- Initialize storage and confirm the backend with
  `StorageManager.get_rdf_backend_identifier()`; it should report `OxiGraph`.

## Traceability


- Modules
  - [src/autoresearch/storage_backends.py][m1]
- Scripts
  - [scripts/oxigraph_backend_sim.py][s1]
- Tests
  - [tests/unit/test_duckdb_storage_backend.py][t1]
  - [tests/unit/test_duckdb_storage_backend_extended.py][t2]
  - [tests/integration/test_rdf_persistence.py][t3]

[m1]: ../../src/autoresearch/storage_backends.py
[s1]: ../../scripts/oxigraph_backend_sim.py
[t1]: ../../tests/unit/test_duckdb_storage_backend.py
[t2]: ../../tests/unit/test_duckdb_storage_backend_extended.py
[t3]: ../../tests/integration/test_rdf_persistence.py
