# Session graph rag integration

## Context
Phase 3 introduces session-scoped knowledge graphs that augment retrieval and
Phase 3 inherits the registry clone fix and semantic fallback guard so the
restored 92.4 % coverage run exercises graph-conditioned planner flows
without `_thread.RLock` reuse or optional dependency crashes. The unit
regressions cover register/update/round-trip snapshots plus the encode
fallback, keeping telemetry stable while GraphRAG work resumes.
【F:src/autoresearch/orchestration/state_registry.py†L18-L148】
【F:tests/unit/orchestration/test_state_registry.py†L21-L138】
【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
【F:src/autoresearch/search/core.py†L147-L199】
【F:tests/unit/search/test_query_expansion_convergence.py†L154-L206】

Automated strict gating and the documented storage resident floor keep release
prerequisites visible while TestPyPI stays paused, and PR4 retrieval exports
GraphML/JSON artifacts with contradiction signals that this issue must extend.
PR5 reverification provides shared audit badges, so session graphs need to feed
verification telemetry alongside planner conditioning.
【F:Taskfile.yml†L62-L104】【F:.github/workflows/ci.yml†L70-L104】
【F:docs/storage_resident_floor.md†L1-L23】
【F:src/autoresearch/knowledge/graph.py†L113-L204】
【F:src/autoresearch/orchestration/reverify.py†L73-L197】

Bootstrap now reuses knowledge-graph instances and skips DuckDB migrations on
subsequent `initialize_storage` calls, ensuring session graphs load without
resetting intermediate state during planner warmups.

surface contradictions for the gate policy. We need to extract entities and
relations from evidence, maintain lightweight graph storage, and expose graph
artifacts plus contradiction signals to the orchestrator.

Storage now attaches contradiction and provenance highlight lists to the
ingestion summary so planner prompts, API responses, and the Streamlit UI can
surface safeguards without recomputing the graph. Behaviour coverage exercises
the "Enable graph exports" toggle to ensure the provenance summary is kept in
sync with generated download payloads.

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
