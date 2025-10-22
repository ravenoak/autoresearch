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

Phase 1 is complete, and the **October 1, 2025** strict and coverage sweeps
confirm the remaining blockers sit inside typed evaluation fixtures and the
`QueryStateRegistry.register` clone. Planner upgrades and GraphRAG expansion now
proceed once the `_thread.RLock` handling and `EvaluationSummary` signature
land, with the new logs capturing the narrowed scope of work and the
**15:27 UTC**
coverage rerun showing the FastEmbed fallback failure after the registry fix.
【F:baseline/logs/mypy-strict-20251001T143959Z.log†L2358-L2377】
【F:baseline/logs/task-coverage-20251001T144044Z.log†L122-L241】
【F:baseline/logs/task-coverage-20251001T152708Z.log†L60-L166】

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
   - Extend reverification controls with configurable retries and
     answer-based claim extraction so operators can refresh audits without
     re-running the full query, while recording attempt counts, extraction
     telemetry, and persistence outcomes for downstream dashboards.
      【F:src/autoresearch/orchestration/reverify.py†L73-L197】
      【F:tests/unit/orchestration/test_reverify.py†L1-L80】
   - Add behavior coverage for the AUTO planner → scout gate → verify loop so
     gate decisions and audit badges stay regression-proof, including CLI
     orchestration to confirm telemetry exposes verification badges end to end.
     The new `@reasoning_modes` scenario locks audit badge propagation into the
     response payload so reverification signals remain visible.
      【F:tests/behavior/features/reasoning_modes.feature†L8-L22】
      【F:tests/behavior/steps/reasoning_modes_steps.py†L1-L40】
   - Record scout gate `coverage_ratio`, agreement score summaries, and the
     normalized decision outcome in `OrchestrationMetrics` and
     `ScoutGateDecision.telemetry`, with regression coverage across the AUTO
     unit and behaviour suites to guard the schema.
   - **Status:** Completed. The September 30 verify and coverage sweeps finish
     through the Task CLI with strict mypy, scout gate telemetry, and the 92.4 %
     statement rate restored, so Phase 1 objectives and evidence trails are all
     green. Fresh **14:28 UTC** `task verify` and **14:30 UTC** `task coverage`
     runs captured after documenting the final-answer audit loop keep the gate
     current while the `QueryState.model_copy` and `A2AMessage` gaps remain
     open. The audit and registry artifacts are now stabilized with direct
     regression coverage guarding the deep-copy path and audit badges across the
     CLI and coordinator tests.
     【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】
     【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
     【F:baseline/logs/task-verify-20250930T142820Z.log†L1-L36】
     【F:baseline/logs/task-coverage-20250930T143024Z.log†L1-L41】
     【F:tests/unit/orchestration/test_state_registry.py†L21-L138】
     【F:tests/unit/orchestration/test_task_coordinator.py†L1-L80】
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
   - **Upcoming deliverables:**
     - Harden planner telemetry exports so `QueryState.set_task_graph`
       persists normalized nodes with warning metadata guarded by
       `tests/behavior/steps/reasoning_mode_steps.py`.
       【F:tests/behavior/steps/reasoning_mode_steps.py†L1-L120】
     - Expand `TaskCoordinator.record_react_step` ordering metadata,
       leveraging the regression assertions already in
       `tests/unit/orchestration/test_task_coordinator.py` to keep
       affinity tie-breakers deterministic.
       【F:tests/unit/orchestration/test_task_coordinator.py†L33-L80】
   - **Acceptance criteria:** Ship typed planner graphs with audited ReAct
     traces, coordinator scheduling that honors affinity tie-breakers, and
     regression coverage that locks telemetry formats before expanding scope.
   - **Prerequisite:** Target the `_thread.RLock` clone and typed
     `EvaluationSummary` fixtures highlighted in the **October 1, 2025** strict
     and coverage sweeps so planner work builds atop a green gate.
     【F:baseline/logs/mypy-strict-20251001T143959Z.log†L2358-L2377】
     【F:baseline/logs/task-coverage-20251001T144044Z.log†L122-L241】
     【F:src/autoresearch/orchestration/state_registry.py†L1-L115】
     【F:tests/unit/orchestration/test_state_registry.py†L1-L112】
3. **Phase 3 – Graph-Augmented Retrieval**
   - Build session-scoped knowledge graphs by extracting entities and
     relations from retrieval snippets and persisting them to DuckDB and
     RDFLib via `KnowledgeGraphPipeline`.
   - Surface contradiction checks to the scout gate through
     `SearchContext.get_contradiction_signal()` while exposing neighbour
     and path queries to agents for multi-hop reasoning.
   - Persist GraphML/JSON exports as knowledge-graph claims so provenance,
     contradiction weights, and export availability flow through
     `SearchContext` and `QueryState.synthesize`, keeping operator telemetry and
     downstream tools in sync.
      【F:src/autoresearch/knowledge/graph.py†L113-L204】
      【F:src/autoresearch/search/context.py†L618-L666】
      【F:src/autoresearch/orchestration/state.py†L1120-L1135】
   - Extend `SearchContext` with on-demand query rewriting, adaptive fetch
     planning, and search self-critique telemetry so retrieval gaps can close
     before debate. These signals surface through `ScoutGateDecision.telemetry`
     when `gate_capture_query_strategy` and
     `gate_capture_self_critique` remain enabled.
     Operators can now tune both gates independently so adaptive attempts and
     critique markers are only persisted when the deployment requires them.
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
6. **Phase 6 – Hierarchical Retrieval Integration**
   - Stand up dual traversal paths: a bottom-up Gecko-style embedding cluster
     builder that grows leaf shards from centroid merges, and a top-down LLM
     partitioner that recursively drafts topical splits. Compare both flows on
     cold-start queries so the system can choose the lower-latency option while
     keeping logarithmic traversal guarantees.
   - Carve the corpus into three summary tiers—flash (≤120 tokens), briefing
     (≤260 tokens), and dossier (≤520 tokens)—and persist the tier metadata on
     every shard so traversal policies can request the shortest viable
     abstraction before expanding to deeper evidence.
   - **Traversal parameters:** Lock an online beam width of 6, a maximum path
     length ℓ = 4, and an EMA weight α = 0.5. The beam size and depth limit
     come from BRIGHT sweep ablations that balanced recall against latency,
     while the EMA weight follows the LATTICE residual-minimizing curve
     documented in the ranking calibration memo.[^ranking-ema]
   - **Evaluation goals:** Calibrate traversal scoring against the BRIGHT
     benchmark uplift (≈9 % Recall@100, ≈5 % nDCG@10 over zero-shot baselines),
     and record domain-level deltas across Business, Research, Infrastructure,
     Government, and Health so regressions surface before rollout.
   - **Telemetry requirements:** Emit `hierarchical_retrieval.traversal_depth`,
     `hierarchical_retrieval.path_score`, summary tier selections, calibration
     residuals, and latency aggregates so dashboards capture depth, error
     bounds, and compute profiles per query.
   - **Dynamic corpus tasks:** Implement a summary refresh queue that enforces
     tier-specific rebuild SLAs, monitor feed-level freshness signals, and fire
     GraphRAG fallbacks whenever new shards arrive without calibrated tiers or
     when traversal residuals exceed the ablation envelope.
   - **Fallback strategy:** Detect out-of-tree corpus updates, trigger
     incremental rebuilds, and fall back to the Phase 3 GraphRAG search path
     whenever calibration confidence drops below the validated threshold.
   - Document operator workflows for enabling the hierarchical retriever,
     including rebuild cadence, calibration replays, dynamic ingestion, and
     dashboard expectations.
   - **Acceptance criteria:** Ship the dual-path prototype, summary tiering,
     calibration validation harness, telemetry stream, nDCG/Recall delta
     capture, and GraphRAG fallback policy backed by regression coverage and
     BRIGHT benchmark comparisons.
   - **Prerequisite:** Requires the prototype tree builder, calibration
     validation, and dynamic-corpus safeguards to reach feature complete status
     before release.
   - **Target release window:** Align with **0.1.1** so integration matures
     after the initial v0.1.0 cut while maintaining audit trails for the release
     dossier. See [LATTICE hierarchical retrieval findings]
     (docs/external_research_papers/arxiv.org/2510.13217v1.md) for benchmark
     details guiding the evaluation goals.

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
- **Planner telemetry contract:** Normalise planner output so
  `PlannerPromptBuilder` requests `sub_questions`, `criteria`, and numeric
  `affinity` fields. Route the structured JSON through
  `TaskGraph.from_planner_output` so top-level objectives and exit criteria
  survive orchestration. Persist telemetry snapshots via
  `QueryState.set_task_graph`, including the new `planner.telemetry` React
  log entry, to make the coordinator hand-off auditable.
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

[^ranking-ema]: See
    [algorithms/ranking_formula.md#exponential-moving-average-path-relevance]
    (algorithms/ranking_formula.md#exponential-moving-average-path-relevance)
    for the residual analysis that sets α.
