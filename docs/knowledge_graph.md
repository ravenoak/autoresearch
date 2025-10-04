# Knowledge graph safeguards

The session-scoped knowledge graph ingests retrieval snippets, extracts
entities and relations, and persists them to the storage layer. After the
storage batch succeeds, the pipeline now builds **contradiction checks** and a
**provenance summary** so downstream components can surface actionable
safeguards in responses.

## Contradiction checks

- The pipeline inspects graph edges for identical subject–predicate pairs that
  point to multiple objects. When detected, it records structured
  contradictions and synthesises human-readable highlights (for example,
  "Contradiction: Battery pack has multiple 'tested_in' relations → Lab
  report, Field diary").
- Search context copies the highlights into planner metadata and exposes them
  through `SearchContext.get_graph_summary()`, allowing API callers and UI
  layers to flag conflicts.

## Provenance summaries

- Every persisted relation records its supporting snippet, source, and export
  claim identifier. The ingestion summary now condenses these records into
  provenance highlights that emphasise sources, snippets, and exported claim
  formats.
- The highlights are stored alongside graph exports, so a single summary gives
  both the contradiction checks and the provenance rationale for how they were
  produced.

## Response integration

- `SearchContext` propagates the highlights into the scout telemetry used by
  planner prompts and into the session summary consumed by the orchestrator.
- `QueryResponse.metrics["knowledge_graph"]` therefore includes the raw
  summary plus the new highlight lists. API responses, CLI tooling, and the
  Streamlit UI can show contradictions, source roll-ups, and export status
  without recomputing the graph.

## UI coverage

- Behaviour scenarios under `tests/behavior/features/streamlit_gui.feature`
  toggle the "Enable graph exports" control and assert that graph export
  downloads are prepared. This keeps the provenance summary and export toggles
  regression-tested alongside the new highlights.
