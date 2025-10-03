# Prepare first alpha release

## Context
As of **October 3, 2025 at 14:52 UTC** the strict typing gate is green but the
pytest suite remains red. `uv run mypy --strict src tests` finishes without
findings, while `uv run --extra test pytest` fails across reverification
configuration, backup scheduling, search caching, API parsing, and FastMCP
handshake fixtures. The [v0.1.0a1 preflight readiness plan](../docs/v0.1.0a1_preflight_plan.md)
summarises the remediation work and maps it to review-sized PRs so we can refresh
coverage evidence and restart the release pipeline.
【4b1e56†L1-L2】【7be155†L104-L262】

TestPyPI dry runs remain paused by default. Once PR-A through PR-D in the
preflight plan land and the suite is green, we will capture fresh verify and
coverage runs before re-enabling the publish stage.
【F:docs/v0.1.0a1_preflight_plan.md†L115-L173】

## Tasks
- [ ] Ship PR-A through PR-D from the preflight plan to restore a green
  pytest suite.
- [ ] Capture fresh verify and coverage logs once the suite passes and
  update release documentation.
- [ ] Re-enable the TestPyPI dry run and document the result after the
  gates are green.
- [ ] Run the release sign-off review with updated evidence and record
  the outcome here.


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
- Record the October 2, 2025 strict pass in the same status surfaces and ensure
  planner Phase 2 delivery resumes only while the strict gate stays green.
- Document the 19:04 UTC `task release:alpha` sweep, ensuring verify, coverage,
  build, and packaging logs stay linked from `CHANGELOG.md`, the release plan,
  and this ticket for auditability.
- Confirm XPASS cleanup and Phase 1 of the deep research initiative remain
  archived in the release plan and deep research plan so the alpha gate reflects
  the current state of evidence.
- Keep the deterministic storage floor documentation linked from the release
  plan, STATUS.md, and TASK_PROGRESS.md while the TestPyPI stage remains
  paused.
- Lift the TestPyPI dry-run hold when the publish directive changes, capture the
  resulting log, and update `docs/release_plan.md` and `STATUS.md` before
  proposing the tag.
- Run the release sign-off review after the publish gate clears, documenting the
  decision and any deferred scope directly in this ticket.

## Status
Open
