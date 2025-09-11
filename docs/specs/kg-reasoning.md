# Kg Reasoning

## Overview

Helper utilities for ontology reasoning and advanced SPARQL queries.

## Algorithms

### register_reasoner
1. Decorator stores the given function under a string key in a module-level
   registry.
2. Subsequent registrations with the same key overwrite the previous entry.

### run_ontology_reasoner
1. Read `storage.ontology_reasoner` from configuration unless an engine is
   provided.
2. Count triples and skip reasoning when the configured maximum is exceeded.
3. Resolve the reasoner:
   - built-in plugin from the registry,
   - dynamically imported `module:function`,
   - otherwise raise `StorageError`.
4. Execute the reasoner once, optionally in a worker thread to honor a
   timeout.
5. Propagate or wrap any exception in `StorageError`.
6. Log completion with the final triple count.

### query_with_reasoning
1. Invoke `run_ontology_reasoner`.
2. Run the supplied SPARQL query against the updated store.

## Invariants

- `register_reasoner` adds exactly one callable per name.
- `run_ontology_reasoner` invokes the selected reasoner at most once and
  never reduces the triple count.
- `run_ontology_reasoner` skips execution when `ontology_reasoner_max_triples`
  is set and exceeded.
- `query_with_reasoning` applies reasoning before evaluation.

## Proof Sketch

- The registry map forces one handler per key, so a single call retrieves the
  desired plugin.
- The worker thread encapsulates reasoner execution, ensuring at most one
  call and enforcing the timeout.
- Triple counts are computed before and after execution; skipping preserves
  the original size, while reasoners typically add new triples.
- `query_with_reasoning` simply delegates, so its guarantees follow from
  `run_ontology_reasoner`.

## Simulation Expectations

Unit tests verify plugin registration, single-invocation semantics, skipping
when the triple cap is exceeded, and query execution after reasoning.

## Traceability

- Modules
  - [src/autoresearch/kg_reasoning.py][m1]
- Tests
  - [tests/unit/test_kg_reasoning.py][t1]

[m1]: ../../src/autoresearch/kg_reasoning.py
[t1]: ../../tests/unit/test_kg_reasoning.py
