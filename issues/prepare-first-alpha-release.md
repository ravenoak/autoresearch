# Prepare first alpha release

## Context
The September 30, 2025 Task CLI runs at 17:45:12 UTC (`task verify`) and
18:19:47 UTC (`task coverage`) both completed with the VSS loader streaming, the
CLI remediation banner in place, and the 92.4 % statement rate restored so the
alpha track can resume without `uv` wrappers.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
We reopened this ticket to coordinate the remaining alpha release work: landing
the deep research initiative phases, capturing the end-to-end `task
release:alpha` sweep, and finalizing docs and packaging guidance before tagging.
`STATUS.md`, `TASK_PROGRESS.md`, `CODE_COMPLETE_PLAN.md`, and
`docs/release_plan.md` now cite the September 30 evidence so roadmap consumers
can follow the CLI and VSS remediation across the repository.
【F:STATUS.md†L21-L59】【F:TASK_PROGRESS.md†L1-L20】【F:CODE_COMPLETE_PLAN.md†L9-L33】【F:docs/release_plan.md†L18-L38】

For historical context, retain
`baseline/logs/task-verify-20250929T035829Z.log` when reviewing the verify
gate—the log shows the final red strict-typing wall in the HTTP layer before we
finished hardening the adapters and CLI. The Taskfile still passes optional
extras through to the embedded `task coverage` call so the configuration mirrors
the standalone sweep, but current gate reviews should prioritize the September
30 evidence now that the strict typing pipeline has recovered.
【F:baseline/logs/task-verify-20250929T035829Z.log†L1-L200】【F:Taskfile.yml†L360-L392】

The September 30, 2025 sweep at 19:04 UTC now completes `task release:alpha`
via the Task CLI, recording the recalibrated scout gate telemetry, CLI path
helper checks, and the refreshed 0.1.0a1 wheels. The verify, coverage, and
build logs are linked from the release plan, changelog, and status rollup so
auditors can trace the alpha evidence without leaving the repo.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
【F:baseline/logs/python-build-20250929T030953Z.log†L1-L13】【F:CHANGELOG.md†L9-L20】

September 30, 2025 01:39 UTC: strict `mypy` over `src` and `tests` still
reports 3,911 historical errors, yet the missing-stub diagnostics for
`fastmcp`, `dspy`, and `PIL.Image` are gone now that the local shims mirror the
extras behaviour. The alpha gate can focus on annotation debt instead of stub
coverage during follow-up sweeps.【d423ea†L2995-L2997】

October 6, 2025: strict typing for the configuration loader, validators, and
Git stub now passes a targeted mypy sweep, unblocking the config milestone for
the alpha gate.【aa0591†L1-L2】

October 9, 2025: the HTTP API middleware and request state now expose explicit
types, and a dedicated mypy sweep plus integration coverage confirm the API
typing gap is closed ahead of the alpha tag.【F:src/autoresearch/api/middleware.py†L18-L169】【F:tests/integration/api/test_middleware_state.py†L1-L91】

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
- Maintain traceability to the September 30, 2025 verify (17:45:12 UTC) and
  coverage (18:19:47 UTC) logs in `STATUS.md`, `TASK_PROGRESS.md`,
  `CODE_COMPLETE_PLAN.md`, and `docs/release_plan.md`, keeping coverage at or
  above the recorded 92.4 % rate.
- Document the 19:04 UTC `task release:alpha` sweep, ensuring verify, coverage,
  build, and packaging logs stay linked from `CHANGELOG.md`, the release plan,
  and this ticket for auditability.
- Confirm XPASS cleanup and Phase 1 of the deep research initiative remain
  archived in the release plan and deep research plan so the alpha gate reflects
  the current state of evidence.
- Lift the TestPyPI dry-run hold when the publish directive changes, capture the
  resulting log, and update `docs/release_plan.md` and `STATUS.md` before
  proposing the tag.
- Run the release sign-off review after the publish gate clears, documenting the
  decision and any deferred scope directly in this ticket.

## Status
Open
