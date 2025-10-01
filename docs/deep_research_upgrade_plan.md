# Deep Research Upgrade Plan

## Overview

This plan translates the September 26, 2025 dialectical review of the
Autoresearch enhancement proposal into actionable work. The approach blends
systems engineering, knowledge management, and human-computer interaction to
keep truthfulness, verifiability, and cost discipline in balance.

## Dialectical Synthesis

- **Thesis:** Adaptive orchestration, per-claim audits, structured planning,
  graph-augmented retrieval, and continuous evaluation will raise factuality
  and research depth.
- **Antithesis:** Each capability risks duplicating current functionality,
  inflating latency, or breaking established workflows and telemetry.
- **Synthesis:** Deliver the upgrades in staged, testable increments with
  guardrails that preserve current guarantees before expanding scope.

## Phase Breakdown

Phase 2 and beyond are paused until the strict typing backlog and evaluation
coverage regression logged in the **September 30, 2025 at 14:55 UTC** `task
verify` run are cleared. Planner upgrades and GraphRAG expansion will restart
only after the tests adopt the widened `EvaluationSummary` signature and the
coverage sweep re-establishes the 92.4 % baseline.
【F:baseline/logs/task-verify-20250930T145541Z.log†L1-L120】
【F:baseline/logs/task-verify-20250930T145541Z.log†L2606-L2617】
【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】

1. **Phase 1 – Adaptive Gate and Claim Audits**
   - Implement the scout pass and gating heuristics with clear metrics.
   - Surface configuration toggles (`gate_policy_enabled`, overlap,
     conflict, and complexity thresholds, plus overrides) so operators can
     tailor the decision boundary.
   - Extend the evidence pipeline to record per-claim support status.
   - Update response formats so clients can render audit tables.
   - Introduce an answer auditor that reviews claim audits before synthesis,
     triggers targeted re-retrieval for unsupported statements, hedges the
     final answer, waits for operator acknowledgment when policies require it,
     and records structured retry provenance for downstream clients.
   - Add audit policy controls (`audit.max_retry_results`,
     `audit.hedge_mode`, `audit.require_human_ack`,
     `audit.operator_timeout_s`, and `audit.explain_conflicts`) so operators can
     balance automation with manual verification before releasing an answer.
   - Add behavior coverage for the AUTO planner → scout gate → verify loop so
     gate decisions and audit badges stay regression-proof, including CLI
     orchestration to confirm telemetry exposes verification badges end to end.
   - **Status:** Completed. The September 30 verify and coverage sweeps finish
     through the Task CLI with strict mypy, scout gate telemetry, and the 92.4 %
     statement rate restored, so Phase 1 objectives and evidence trails are all
     green. Fresh **14:28 UTC** `task verify` and **14:30 UTC** `task coverage`
     runs captured after documenting the final-answer audit loop keep the gate
     current while the `QueryState.model_copy` and `A2AMessage` gaps remain
     open.
     【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】
     【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
     【F:baseline/logs/task-verify-20250930T142820Z.log†L1-L36】
     【F:baseline/logs/task-coverage-20250930T143024Z.log†L1-L41】
   - **Acceptance criteria:** Keep the Task CLI verify and coverage stages
     publishing scout-gate telemetry and audit tables, and maintain coverage at
     or above 92.4 % while TestPyPI remains deferred under the release gate.
2. **Phase 2 – Planner and Coordinator Evolution**
   - Promote planner outputs into a schedulable task graph.
   - Capture ReAct traces for transparency and replay.
   - Document interfaces for specialized agents and tool calls.
   - Refine `agents/specialized/planner.py` prompts so decomposition yields
     typed `TaskGraph` nodes with tool affinity scores instead of spawning
     new agents.
   - Extend `orchestration/coordinator.py` scheduling rules to consume
     those affinities while reusing the existing coordinator instance.
   - **Acceptance criteria:** Ship typed planner graphs with audited ReAct
     traces, coordinator scheduling that honors affinity tie-breakers, and
     regression coverage that locks telemetry formats before expanding scope.
   - **Prerequisite:** Unblocked. The strict typing backlog and evaluation
     harness regression cited in the **14:55 UTC** log are now guarded by the
     registry cloning tests and strict typing helpers, so planner work can
     resume.
     【F:baseline/logs/task-verify-20250930T145541Z.log†L1-L120】
     【F:baseline/logs/task-verify-20250930T145541Z.log†L2606-L2617】
     【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
     【F:src/autoresearch/orchestration/state_registry.py†L1-L115】
     【F:tests/unit/orchestration/test_state_registry.py†L1-L112】
3. **Phase 3 – Graph-Augmented Retrieval**
   - Build session-scoped knowledge graphs by extracting entities and
     relations from retrieval snippets and persisting them to DuckDB and
     RDFLib via `KnowledgeGraphPipeline`.
   - Surface contradiction checks to the scout gate through
     `SearchContext.get_contradiction_signal()` while exposing neighbour
     and path queries to agents for multi-hop reasoning.
   - Instrument `OrchestrationMetrics` with Prometheus-backed
     `graph_ingestion` telemetry (entity, relation, contradiction, neighbour,
     and latency aggregates) guarded by `search.context_aware` toggles so
     operators can monitor GraphRAG uptake.
   - Export lightweight GraphML or JSON artifacts via the output formatter
     so downstream tools can visualise graph state per session.
   - Document how to toggle
     `search.context_aware.planner_graph_conditioning` for planner prompts,
     and cover the cues with
     `tests/behavior/features/reasoning_modes/`
     `planner_graph_conditioning.feature` so regression sweeps keep
     contradiction and neighbour hints intact.
   - **Acceptance criteria:** Deliver contradiction checks wired into the scout
     gate, persist exportable session graphs, and lock telemetry dashboards that
     report ingestion and contradiction metrics under the context-aware toggles.
   - **Prerequisite:** Blocked behind the same strict typing and coverage work
     as Phase 2 so planner telemetry and graph exports build on a green harness.
4. **Phase 4 – Evaluation Harness and Layered UX**
   - Automate TruthfulQA, FEVER, and HotpotQA smoke runs with KPIs.
   - Add layered summaries, Socratic prompts, per-claim audit toggles, and
     claim badge guidance to the UI.
   - Ensure CLI and GUI share consistent depth controls and expose the same
     planner depth and routing metrics in CSV/Parquet exports.
   - **Acceptance criteria:** Establish automated benchmark sweeps with
     published KPIs, synchronize layered UX controls across CLI and GUI,
     deliver interactive claim re-verification across UI/CLI/API, and export
     regression-ready CSV/Parquet artifacts with audited schemas.
   - **Prerequisite:** Requires the strict typing backlog and
     `EvaluationSummary` regression to be resolved so documentation, harness
     CSVs, and metrics stay aligned.
5. **Phase 5 – Cost-Aware Model Routing**
   - Assign models per role with budget-aware fallbacks.
   - Monitor token, latency, and accuracy metrics for regressions.
   - Publish tuning guides for operators.
   - Persist routing decisions, overrides, and the active strategy via
     `persist_model_routing_metrics` so dashboards can chart savings without
     replaying runs. Initial simulations report roughly two currency units of
     savings for the `cost_saver` policy while still logging gate-driven
     escalations to premium models.
     【F:tests/performance/test_budget_router.py†L103-L152】
   - **Acceptance criteria:** Prove budget routing stability with telemetry and
     savings dashboards, document operator override flows, and maintain tests
     that guard role-based fallbacks across regression suites.
   - **Prerequisite:** Defer until strict typing debt and evaluation coverage
     regressions clear so routing instrumentation layers onto a stable baseline.

## Cross-Cutting Requirements

- Capture decision rationales in code comments, docs, and issues.
- Maintain diagrams and pseudo-code as interfaces evolve.
- Record benchmark and cost results in STATUS.md and TASK_PROGRESS.md.
- Keep lines under 80 characters and cite sources in new documentation.

## Immediate Deliverables

- Roadmap, status, and changelog updates that describe the phased plan.
- Issues tracking the adaptive gate, evidence pipeline, and GraphRAG work.
- Specification and pseudo-code revisions covering the new components.
- Bench harness architecture notes to unblock implementation in Phase 4.

## Next Steps

Complete the documentation and issue updates described above, then begin
Phase 2 implementation under the new tickets while monitoring cost and
accuracy.

## Planner and Coordinator Implementation Map

- **Socratic prompt calibration (Planner):**
  - Question: How do we surface decomposition intent without multiplying
    agents?
  - Answer: Update `PlannerPromptBuilder` in
    `agents/specialized/planner.py` to ask for explicit task objectives,
    required tools, and exit criteria in a single ReAct-style table.
    Encode the result as structured JSON so
    `TaskGraph.from_planner_output` can hydrate nodes without extra
    adapters.
  - Counterpoint: Could free-form language capture nuance better? No,
    because downstream scheduling relies on typed fields; keep free-form
    rationale in a separate `explanation` column that does not affect
    routing.
- **Dialectical graph shaping (Coordinator):**
  - Question: Should `TaskCoordinator` branch into per-tool
    coordinators?
  - Answer: No. Amend `TaskCoordinator.schedule_next` in
    `orchestration/coordinator.py` to order nodes by dependency readiness
    and the planner-provided tool affinity score. Maintain a single
    coordinator and augment the logic with a deterministic tie-breaker on
    dependency depth to keep behavior reproducible.
  - Counterpoint: Would a brand-new coordinator be simpler? Reject that
    impulse; integrating within the current class preserves telemetry and
    keeps regression risk bounded.

## ReAct Telemetry and Test Hooks

- **`QueryState.set_task_graph`:** Layer a lightweight `react_log` append
  that stores the planner prompt, structured response, and normalization
  warnings so subsequent `TaskCoordinator` calls can replay the reasoning
  chain.
- **`TaskCoordinator.record_react_step`:** Extend the method to include
  task node identifiers, tool affinity deltas, and downstream task unlock
  events in each log entry. Keep the signature stable by packing additions
  into the existing metadata dictionary.
- **Testing impact:**
  - Update `tests/unit/orchestration/test_task_coordinator.py` to assert
    the new metadata keys and tie-breaker ordering.
  - Expand `tests/unit/test_query_state_features.py` to cover
    `react_log` persistence when the task graph is replaced.
  - Introduce scenario coverage in
    `tests/behavior/steps/reasoning_mode_steps.py` so multi-step runs
    verify the planner-coordinator hand-off with ReAct telemetry enabled.

## KPI Tracking for Iterative Delivery

- **Multi-step task coverage:** Track the proportion of tasks with depth
  >1 that successfully log planner decomposition and coordinator execution
  per run of `task verify`. Target ≥75% coverage before widening scope.
- **Tool affinity accuracy:** Measure how often the selected tool matches
  the planner's top-ranked choice. Record baselines in `STATUS.md` and aim
  for ≥85% agreement once telemetry is wired.
- **ReAct replay latency:** Monitor the time to reconstruct a task run
  from the new logs. Maintain <200 ms overhead per task to avoid
  regressions.
- **Telemetry completeness:** Use docstring-driven audits in
  `orchestration/coordinator.py` to ensure every scheduled node includes a
  `react_log` reference. Audit results quarterly and publish deltas in
  `TASK_PROGRESS.md`.
