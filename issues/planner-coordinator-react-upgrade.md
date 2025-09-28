# Planner coordinator react upgrade

## Context
Phase 2 of the deep research program promotes the planner output into a
structured task graph that the coordinator can schedule deterministically while
logging ReAct traces. We need richer prompts, tool affinity metadata, and
telemetry hooks so decomposition quality and routing choices remain auditable.

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)
- [adaptive-gate-and-claim-audit-rollout](adaptive-gate-and-claim-audit-rollout.md)

## Acceptance Criteria
- Planner prompt templates request objectives, tool affinity scores, exit
  criteria, and rationale, emitting structured data the coordinator can ingest
  without additional parsing.
- TaskCoordinator honors tool affinity scores, enforces dependency ordering, and
  records routing decisions plus ReAct steps with task identifiers.
- QueryState persists the canonical task graph and exposes planner/coordinator
  telemetry for replay.
- Unit, integration, and behavior tests cover planner output normalization,
  scheduler tie-breakers, and ReAct log persistence.
- Documentation updates in `docs/orchestration.md` and `docs/pseudocode.md`
  explain the new data structures and replay workflow.

## Status
Open
