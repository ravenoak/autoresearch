# Session graph rag integration

## Context
Phase 3 introduces session-scoped knowledge graphs that augment retrieval and
surface contradictions for the gate policy. We need to extract entities and
relations from evidence, maintain lightweight graph storage, and expose graph
artifacts plus contradiction signals to the orchestrator.

## Dependencies
- [planner-coordinator-react-upgrade](planner-coordinator-react-upgrade.md)

## Acceptance Criteria
- Graph construction pipeline ingests retrieval snippets, extracts entities and
  relations, and persists them to DuckDB and RDF stores with provenance.
- Gate policy and planner surfaces receive contradiction signals and neighbor
  context derived from the session graph.
- Export functionality produces GraphML or JSON artifacts with metadata that
  downstream tools can consume.
- Telemetry captures graph size, build latency, and contradiction triggers for
  evaluation runs.
- Documentation updates in `docs/specification.md`, `docs/search_backends.md`,
  and `docs/deep_research_upgrade_plan.md` describe graph usage patterns and
  guardrails.

## Status
Open
