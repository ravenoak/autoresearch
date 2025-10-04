# Planner coordinator react upgrade

## Context
Phase 2 of the deep research program promotes the planner output into a typed
task graph that captures dependency depth and Socratic self-check prompts. The
registry clone fix that deep-copies QueryState snapshots with typed memo support
and the semantic fallback guard that keeps coverage green when fastembed is
absent both landed earlier. The regression suites cover register/update/round-
trip flows plus the encode fallback, so planner telemetry can rely on restored
coverage while strict typing proceeds.
【F:src/autoresearch/orchestration/state_registry.py†L18-L148】
【F:tests/unit/orchestration/test_state_registry.py†L21-L138】
【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
【F:src/autoresearch/search/core.py†L147-L199】
【F:tests/unit/search/test_query_expansion_convergence.py†L154-L206】

Automated strict gating now runs through `task mypy-strict` in both the Task CLI
and CI workflow, and the deterministic storage resident floor is documented for
release reviewers while the TestPyPI stage remains paused. PR5 reverification
and PR4 retrieval exports supply shared telemetry—verification badges,
contradiction signals, and export flags—that the planner must consume once the
typed harness clears.
【F:Taskfile.yml†L62-L104】【F:.github/workflows/ci.yml†L70-L104】
【F:docs/storage_resident_floor.md†L1-L23】
【F:src/autoresearch/orchestration/reverify.py†L73-L197】
【F:src/autoresearch/search/context.py†L618-L666】

structured task graph that the coordinator can schedule deterministically while
logging ReAct traces. We need richer prompts, tool affinity metadata, and
telemetry hooks so decomposition quality and routing choices remain auditable.

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)
- [adaptive-gate-and-claim-audit-rollout](adaptive-gate-and-claim-audit-rollout.md)

## Acceptance Criteria
- Planner prompt templates request objectives, tool affinity scores, exit
  criteria, dependency depth, and Socratic self-check prompts, emitting
  structured data the coordinator can ingest without additional parsing.
- TaskCoordinator honors tool affinity scores, planner-provided dependency
  depth, and records routing decisions plus ReAct steps with task identifiers
  and dependency rationale.
- QueryState persists the canonical task graph and exposes planner/coordinator
  telemetry for replay.
- Unit, integration, and behavior tests cover planner output normalization,
  scheduler tie-breakers, and ReAct log persistence.
- Documentation updates in `docs/orchestration.md`, `docs/pseudocode.md`, and
  refreshed diagrams explain the PRDV flow, dependency depth, and replay
  workflow.

## Checklist
- [x] Capture the strict typing prerequisite for Phase 2 in
  `docs/deep_research_upgrade_plan.md` so planner work pauses until the
  **14:55 UTC** `task verify` failures clear.
- [x] Update `docs/pseudocode.md` with the PRDV verification loop and expanded
  `EvaluationSummary` fields to align planner telemetry with verification docs.
- [x] Normalise planner metadata into result payloads and coordinator traces so
  `task_metadata` mirrors planner hints without bespoke adapters.
- [x] Resume implementation after the **October 1, 2025** strict and coverage
  sweeps confirm the `_thread.RLock` clone and typed `EvaluationSummary`
  fixtures are green again.
  【F:baseline/logs/mypy-strict-20251001T143959Z.log†L2358-L2377】
  【F:baseline/logs/task-coverage-20251001T144044Z.log†L122-L241】

## Status
Open
