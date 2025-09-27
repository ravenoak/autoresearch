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

## Planned Enhancements

### Extend ingestion without duplicating stores
- Stage feature extraction inside `KnowledgeGraphPipeline.ingest` before the
  persistence call so contradiction statistics, provenance confidence, and
  temporal decay are attached to each `GraphRelation` in-memory.
- Reuse `StorageManager.update_knowledge_graph` for the full batch so DuckDB,
  NetworkX, and RDFLib all observe identical feature maps instead of shadow
  caches that would drift under concurrent ingestion.
- Expand the ingestion summary to record the applied feature schema, but defer
  persistence until `StorageManager` confirms the batch succeeded; this guards
  against partial updates that would desynchronise contradiction metrics.
- Dialectical trade-off: a separate feature graph could specialise indexes for
  analytics, yet it would double write volume and complicate invalidation.
  Extending the shared pipeline keeps latency bounded to a single round-trip
  while leveraging existing transactional semantics.

### Improve contradiction scoring and accessors
- Update `_detect_contradictions` to compute a normalised disagreement weight
  per `(subject, predicate, object)` tuple using evidence counts and recency so
  `GraphContradiction` encapsulates both magnitude and freshness.
- Store the resulting weights alongside adjacency metadata that powers
  `neighbors`, `graph_paths`, and future path scoring helpers; caching them in
  the shared store prevents recomputation when downstream components request
  repeated traversals.
- Add optional `include_contradictions` and `min_weight` parameters to accessor
  methods so callers can surface, filter, or suppress conflicting edges without
  breaking existing signatures.
- Socratic reflection: do weighted contradictions introduce cognitive load for
  consumers? The alternative binary flag is simpler, yet weighted outputs let
  ranking heuristics reason about gradations of disagreement, which downstream
  rerankers already expect.

### SearchContext integration points
- Cache the enhanced ingestion summary on `SearchContext` and expose it through
  typed accessors that reveal contradiction scores, edge weights, and last
  update timestamps to the orchestrator layer.
- Feed contradiction weights into scout gating by scaling existing novelty or
  reliability heuristics; low-weight contradictions reduce risk of pruning
  promising leads, while high-weight conflicts throttle expansions.
- Thread the neighbour annotations into `SearchContext.entities` so entity
  enrichment can down-weight contentious relations during prompt assembly.
- Alternatives explored: pushing feedback loops solely into orchestrator level
  would limit the tight control loop between retrieval and reasoning, whereas
  local integration keeps the signal near its source and simplifies auditing.

### Schema and performance adjustments in `kg_reasoning.py`
1. Extend `GraphRelation.to_payload` plus storage schema bindings to accept a
   `features` dictionary with typed keys for contradiction, confidence, and
   decay weights, preserving default empties for backwards compatibility.
2. Update `GraphExtractionSummary` to memoise aggregate contradiction scores
   and per-predicate weight histograms; expose lazily evaluated properties so
   repeated reads avoid recomputing statistics.
3. Refactor `_derive_multi_hop_paths` to stream from the shared NetworkX graph
   without materialising duplicate structures and to reuse cached contradiction
   weights when scoring paths, keeping CPU costs aligned with current budgets.
4. Guard per-edge caches with `_summary_lock` and add lightweight version
   counters so concurrent readers can detect updates without blocking, trading
   minimal bookkeeping for predictable latency.

### Regression testing strategy
- Unit: mock `StorageManager.update_knowledge_graph` to assert each relation
  payload now includes the feature dictionary and that ingestion summaries are
  withheld until the mock reports success, preventing accidental duplicate
  store creation.
- Integration: execute ingestion against the in-memory backend, then verify
  `SearchContext` exposes contradiction-weighted neighbours and that scout
  gating consumes the signal during expansion ranking.
- Property-based: synthesise snippets that yield overlapping predicates with
  conflicting objects and confirm contradiction weights stay in `[0, 1]` while
  accessor filters honour `min_weight` thresholds.
- Performance guardrails: extend existing benchmarks with assertions over path
  derivation latency and lock contention counters, ensuring memoisation keeps
  ingestion within the current service-level objectives.

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
