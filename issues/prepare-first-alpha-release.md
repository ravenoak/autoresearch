# Prepare first alpha release

## Context
The September 30, 2025 Task CLI runs at 17:45 UTC (`task verify`) and 18:19 UTC
(`task coverage`) now anchor `task release:alpha`, with the 02:54 UTC build,
twine check, and TestPyPI dry run logs keeping the packaging trail auditable.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】
【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
【F:baseline/logs/build-20250929T025418Z.log†L1-L12】
【F:baseline/logs/twine-check-20250929T025438Z.log†L1-L2】
【F:baseline/logs/publish-dev-20250929T025443Z.log†L1-L13】
This ticket coordinates the final alpha release readiness steps: maintaining the
log cross-links, recording the Phase 1 gating closure, and carrying the updated
scope notes into `docs/deep_research_upgrade_plan.md`. `STATUS.md`,
`TASK_PROGRESS.md`, and `docs/release_plan.md` reference the evidence so the
release committee can follow the remediation narrative without re-running the
pipeline.
【F:STATUS.md†L21-L38】【F:TASK_PROGRESS.md†L1-L17】【F:docs/release_plan.md†L18-L33】
The archived Phase 1 issue captures the adaptive gate resolution for posterity
and links back to these logs.
【F:issues/archive/adaptive-gate-and-claim-audit-rollout.md†L1-L38】

## Dependencies
- [coordinate-deep-research-enhancement-initiative](coordinate-deep-research-enhancement-initiative.md)
- [adaptive-gate-and-claim-audit-rollout](archive/adaptive-gate-and-claim-audit-rollout.md)
- [deliver-evidence-pipeline-2-0](deliver-evidence-pipeline-2-0.md)
- [planner-coordinator-react-upgrade](planner-coordinator-react-upgrade.md)
- [session-graph-rag-integration](session-graph-rag-integration.md)
- [evaluation-and-layered-ux-expansion](evaluation-and-layered-ux-expansion.md)
- [roll-out-layered-ux-and-model-routing](roll-out-layered-ux-and-model-routing.md)
- [build-truthfulness-evaluation-harness](build-truthfulness-evaluation-harness.md)
- [cost-aware-model-routing](cost-aware-model-routing.md)

## Acceptance Criteria
- Deep research initiative issues listed above are closed or explicitly deferred
  with documented scope reductions before the alpha tag is proposed.
- An end-to-end `task release:alpha` run succeeds via the Task CLI with logs
  archived under `baseline/logs/` and referenced from `STATUS.md` and the
  release plan.
- `CHANGELOG.md` contains release notes for `0.1.0a1` that link to the final
  verify, coverage, build, and publish logs.
- `docs/release_plan.md`, `STATUS.md`, and `TASK_PROGRESS.md` remain synchronized
  with the latest gate evidence through the release sign-off meeting.
- Packaging and installation guidance highlights the restored Task CLI targets
  and the VSS extension handling required for the alpha workflow.

## Status
Open
