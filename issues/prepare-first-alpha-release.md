# Prepare first alpha release

## Context
The September 30, 2025 Task CLI runs at 17:45 UTC (`task verify`) and 18:19 UTC
(`task coverage`) both completed with the VSS loader streaming and the CLI fix
banner in place, so the alpha track can resume without `uv` wrappers.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
We reopened this ticket to coordinate the remaining alpha release work: landing
the deep research initiative phases, capturing the end-to-end `task
release:alpha` sweep, and finalizing docs and packaging guidance before tagging.
`STATUS.md`, `TASK_PROGRESS.md`, and `docs/release_plan.md` now cite the new logs
so roadmap consumers can follow the remediation of the CLI and VSS regressions.
【F:STATUS.md†L21-L29】【F:TASK_PROGRESS.md†L1-L10】【F:docs/release_plan.md†L19-L27】

Auditors should now pull
`baseline/logs/task-verify-20250929T035829Z.log` when reviewing the verify gate;
the run prints the `[verify][lint]` and `[verify][mypy]` success banners before
strict typing fails in `src/git` and the Streamlit UI, and the Taskfile now
passes optional extras through to the embedded `task coverage` call so the
coverage configuration mirrors the standalone sweep once these strict errors
clear.【F:baseline/logs/task-verify-20250929T035829Z.log†L1-L60】【F:baseline/logs/task-verify-20250929T035829Z.log†L80-L200】
【F:Taskfile.yml†L360-L392】

The September 30, 2025 sweep at 19:04 UTC now completes `task release:alpha`
via the Task CLI, recording the recalibrated scout gate telemetry, CLI path
helper checks, and the refreshed 0.1.0a1 wheels. The verify, coverage, and
build logs are linked from the release plan, changelog, and status rollup so
auditors can trace the alpha evidence without leaving the repo.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
【F:baseline/logs/python-build-20250929T030953Z.log†L1-L13】【F:CHANGELOG.md†L9-L20】

## Dependencies
- [coordinate-deep-research-enhancement-initiative](coordinate-deep-research-enhancement-initiative.md)
- [adaptive-gate-and-claim-audit-rollout](adaptive-gate-and-claim-audit-rollout.md)
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
