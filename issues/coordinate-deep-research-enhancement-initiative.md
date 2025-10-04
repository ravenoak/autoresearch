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

## Acceptance Criteria
- Phased work items (issues, docs, roadmap) exist for each enhancement area.
- STATUS.md and ROADMAP.md cross-reference the initiative and phase ordering.
- Documentation and pseudo-code describe the new components ahead of
  implementation.
- Resource, risk, and schedule updates are reported in STATUS.md after each
  phase checkpoint.
- Completion criteria are reviewed with project maintainers before phase
  transitions.

## Status
Open
