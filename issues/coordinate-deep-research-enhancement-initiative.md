# Coordinate deep research enhancement initiative

## Context
We adopted the September 26, 2025 dialectical plan that sequences adaptive
gating, per-claim audits, planner upgrades, GraphRAG, evaluation harnesses, and
cost-aware routing. Execution requires coordinated scheduling across existing
roadmap milestones, documentation updates, and telemetry tracking. Phase 1 is
now complete; the release sweep and deep research plan confirm the gate and
audit telemetry ship in the alpha pipeline while later phases remain in flight.
The **October 1, 2025** strict and coverage reruns narrow the remaining debt to
typed evaluation fixtures and the `_thread.RLock` registry clone, keeping the
planner and GraphRAG dependencies explicit while Phase 2 spins up.
【F:docs/deep_research_upgrade_plan.md†L27-L58】
【F:baseline/logs/mypy-strict-20251001T143959Z.log†L2358-L2377】
【F:baseline/logs/task-coverage-20251001T144044Z.log†L122-L241】
Scout gate telemetry now exports coverage ratios, agreement summaries, and a
normalized decision outcome through `OrchestrationMetrics` so dashboards can
track AUTO escalations without replaying runs.
【F:docs/orchestration.md†L24-L31】【F:docs/deep_research_upgrade_plan.md†L52-L58】

The AUTO scout snapshots now freeze synthesiser claims before telemetry export,
and both unit and behaviour suites assert that every sample carries a non-empty
immutable claim payload. This guards against parallel merge mutation while the
gate policy reasons over agreement metrics.
【F:src/autoresearch/orchestration/metrics.py†L180-L220】【F:src/autoresearch/orchestration/orchestrator.py†L190-L280】
【F:tests/unit/orchestration/test_auto_mode.py†L90-L135】【F:tests/behavior/steps/reasoning_modes_auto_steps.py†L350-L375】

Phase 6 introduces hierarchical retrieval built on a prototype semantic tree,
calibration validation harness, and dynamic-corpus safeguards before default
rollout. Telemetry will extend to traversal depth, path scoring, calibration
residuals, and GraphRAG fallback triggers so operators can track integration
health. Benchmark targets match the ≈9 % Recall@100 and ≈5 % nDCG@10 BRIGHT
uplift documented for LATTICE, guiding the evaluation envelope for the release
window targeted at **0.1.1**.
【F:docs/deep_research_upgrade_plan.md†L125-L150】
【F:docs/release_plan.md†L63-L108】
【F:STATUS.md†L15-L32】

`task check` and `task verify` now invoke `task mypy-strict` directly, giving the
initiative an automated strict gate in every local run while the CI workflow
keeps the TestPyPI flag paused by default. The deterministic storage resident
floor is documented for release reviewers, and PR5/PR4 upgrades ship the
reverification loop plus session-graph exports so later phases build on shared
telemetry.
【F:Taskfile.yml†L62-L104】【F:.github/workflows/ci.yml†L70-L104】
【F:docs/storage_resident_floor.md†L1-L23】
【F:src/autoresearch/orchestration/reverify.py†L73-L197】
【F:src/autoresearch/knowledge/graph.py†L113-L204】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)
- [hierarchical-retrieval-lattice-integration](hierarchical-retrieval-lattice-integration.md)
- [summary-refresh-automation](summary-refresh-automation.md) – captures the
  calibration-driven summary refresh pipeline.
- [calibration-telemetry-dashboards](calibration-telemetry-dashboards.md) –
  tracks dashboards derived from the calibration outputs.

## Phase 6 tasks
- Land the prototype semantic tree builder and calibration harness tracked in
  [hierarchical-retrieval-lattice-integration](hierarchical-retrieval-lattice-integration.md).
- Instrument telemetry for `hierarchical_retrieval.traversal_depth`,
  `hierarchical_retrieval.path_score`, calibration residuals, and fallback
  counters so STATUS.md and ROADMAP.md receive live signals.
- Document the fallback playbook that routes queries back to Phase 3 GraphRAG
  whenever calibration confidence drops below validated thresholds or dynamic
  corpus updates exceed guardrails.
- Schedule evaluation checkpoints that reproduce the ≈9 % Recall@100 and ≈5 %
  nDCG@10 BRIGHT uplift reported for LATTICE before enabling the feature by
  default.
- Maintain the Phase 6 checklist below, ensuring staging verification of
  beam/ℓ/α defaults, calibration residual monitoring thresholds, and
  dynamic-corpus fallback exercises complete ahead of the production cutover.
- Schedule cross-team reviews with platform, evaluation, and infra leads to
  confirm Gemini 2.5-flash access readiness and to compare BRIGHT replication
  runs against the ±1 % tolerance band before sign-off.

### Phase 6 checklist
- [ ] Verify beam/ℓ/α defaults in staging, including telemetry snapshots before
      and after the cutover rehearsal.
- [ ] Monitor calibration residual thresholds continuously in staging and
      document alerting hooks for dashboard consumers.
- [ ] Exercise dynamic-corpus fallback drills that validate GraphRAG downgrade
      triggers and operator playbooks.

## Acceptance Criteria
- Phased work items (issues, docs, roadmap) exist for each enhancement area.
- STATUS.md and ROADMAP.md cross-reference the initiative and phase ordering.
- Documentation and pseudo-code describe the new components ahead of
  implementation.
- Resource, risk, and schedule updates are reported in STATUS.md after each
  phase checkpoint, including Phase 6 telemetry readiness.
- Completion criteria are reviewed with project maintainers before phase
  transitions.
- Hierarchical retrieval workstreams (tree builder, calibration validation,
  dynamic-corpus safeguards) are scheduled, tracked, and evaluated against the
  LATTICE benchmark targets before the Phase 6 release window.
- Telemetry and fallback playbooks cover the GraphRAG downgrade path and are
  published alongside operator enablement guidance.
- Evaluation checkpoints document BRIGHT metric deltas (≈9 % Recall@100, ≈5 %
  nDCG@10) prior to launch, with regressions triggering the recorded fallback
  strategy.

## Status
Open
