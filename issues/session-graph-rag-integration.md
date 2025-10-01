# Session graph rag integration

## Context
Phase 3 introduces session-scoped knowledge graphs that augment retrieval and
surface contradictions for the gate policy. We need to extract entities and
relations from evidence, maintain lightweight graph storage, and expose graph
artifacts plus contradiction signals to the orchestrator.

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)
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

## QA Coverage

- Scenario coverage in
  `tests/behavior/features/reasoning_modes/planner_graph_conditioning.feature`
  now exercises planner graph conditioning prompts and telemetry so graph
  signals stay regression-proof.

## Checklist
- [x] Note in `docs/deep_research_upgrade_plan.md` that Phase 3 is blocked by
  the **14:55 UTC** `task verify` strict-typing failure and coverage backlog.
- [x] Align PRDV telemetry docs (performance and pseudocode) with the expanded
  `EvaluationSummary` fields needed for GraphRAG exports.
- [ ] Resume GraphRAG work after the **October 1, 2025** strict and coverage
  sweeps show the `_thread.RLock` registry clone and typed `EvaluationSummary`
  fixtures are passing so the 92.4 % coverage run can repeat.
  【F:baseline/logs/mypy-strict-20251001T143959Z.log†L2358-L2377】
  【F:baseline/logs/task-coverage-20251001T144044Z.log†L122-L241】

## Status
Open
