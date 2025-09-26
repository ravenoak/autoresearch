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

### KnowledgeGraphPipeline.ingest
1. Skip work when graph ingestion is disabled via
   `search.context_aware.graph_pipeline_enabled`.
2. Normalise sentences from retrieval snippets and extract candidate relations
   using heuristics for verb phrases (`discovered`, `was born in`, etc.).
3. Deduplicate entities with hashed identifiers and cap totals by
   `graph_max_entities` and `graph_max_edges`.
4. Persist entities and relations through `StorageManager` into DuckDB,
   NetworkX, and RDFLib, emitting triples such as `urn:kg:<subject>`.
5. Derive contradictions when identical subjects and predicates map to
   different objects, and compute multi-hop paths via NetworkX.
6. Cache a summary containing entity counts, relation counts, contradictions,
   multi-hop paths, and a contradiction score for downstream consumers.

### KnowledgeGraphPipeline.graph_paths
1. Resolve entity identifiers by case-insensitive label matching.
2. Traverse the knowledge graph as an undirected view to discover simple paths
   between the requested endpoints, respecting the configured depth cutoff.
3. Return paths as ordered label lists suitable for multi-hop reasoning or
   explanation traces.

## Invariants

- `register_reasoner` adds exactly one callable per name.
- `run_ontology_reasoner` invokes the selected reasoner at most once and
  never reduces the triple count.
- `run_ontology_reasoner` skips execution when `ontology_reasoner_max_triples`
  is set and exceeded.
- `query_with_reasoning` applies reasoning before evaluation.
- `KnowledgeGraphPipeline.ingest` never emits more than the configured maximum
  entities or relations per batch and always records summaries even when no
  edges are extracted.
- Knowledge graph contradiction scores are derived from persisted edges and
  remain in `[0, 1]`.

## Proof Sketch

- The registry map forces one handler per key, so a single call retrieves the
  desired plugin.
- The worker thread encapsulates reasoner execution, ensuring at most one
  call and enforcing the timeout.
- Triple counts are computed before and after execution; skipping preserves
  the original size, while reasoners typically add new triples.
- `query_with_reasoning` simply delegates, so its guarantees follow from
  `run_ontology_reasoner`.
- Entity hashing ensures deterministic identifiers, so duplicates collapse
  safely before persistence.
- Knowledge graph persistence routes through `StorageManager`, guaranteeing
  RDFLib, DuckDB, and NetworkX remain in sync.
- Contradiction detection groups edges by subject and predicate; multiple
  targets increase the contradiction count and the normalised score.

## Simulation Expectations

Unit tests verify plugin registration, single-invocation semantics, skipping
when the triple cap is exceeded, and query execution after reasoning. New
integration tests assert that ingestion yields multi-hop paths and that
contradictions influence orchestrator heuristics.

## Traceability

- Modules
  - [src/autoresearch/kg_reasoning.py][m1]
- Tests
  - [tests/unit/test_kg_reasoning.py][t1]
  - [tests/integration/test_knowledge_graph_pipeline.py][t2]

[m1]: ../../src/autoresearch/kg_reasoning.py
[t1]: ../../tests/unit/test_kg_reasoning.py
[t2]: ../../tests/integration/test_knowledge_graph_pipeline.py
