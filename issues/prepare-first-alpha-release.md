# Prepare first alpha release

## Context
As of **October 4, 2025 at 05:34 UTC** the strict typing gate remains green:
`uv run mypy --strict src tests` again reported “Success: no issues found in
790 source files”, so we can focus on the remaining pytest regressions before
rerunning the full release sweep.【c2f747†L1-L2】 A targeted `uv run --extra
test pytest` sample at **05:31 UTC** still reproduces the legacy search stub
fallback drift and guides the PR-C scope.【81b49d†L25-L155】【81b49d†L156-L204】
【ce87c2†L81-L116】

The follow-up release sweeps confirm the lint sweep landed and that PR-C’s
instrumentation work is in place. At **14:44 UTC** `uv run task verify
EXTRAS="nlp ui vss git distributed analysis llm parsers"` prints
`[verify][lint] flake8 passed`, clears strict mypy, and shows both legacy and
VSS parameterisations of
`tests/unit/test_core_modules_additional.py::test_search_stub_backend`
passing before `tests/unit/test_failure_scenarios.py::
test_external_lookup_fallback` fails with an empty placeholder URL.
【F:baseline/logs/task-verify-20251004T144057Z.log†L167-L169】【F:baseline/logs/task-verify-20251004T144057Z.log†L555-L782】
The paired coverage sweep at **14:45 UTC** stops on the same assertion, so the
preflight plan now treats the deterministic fallback URL as the last PR-C step
before coverage can refresh.
【F:baseline/logs/task-coverage-20251004T144436Z.log†L481-L600】【F:docs/v0.1.0a1_preflight_plan.md†L10-L239】

TestPyPI dry runs remain paused; once the fallback fix lands we will capture
fresh verify and coverage logs and re-enable the publish stage before the next
release sign-off.【F:docs/v0.1.0a1_preflight_plan.md†L10-L239】

## Tasks
- [ ] Finish PR-C by restoring the deterministic fallback URL so the
  remaining search failure clears.
- [x] Confirm the lint sweep landed via the latest `task verify` run.
- [ ] Ship PR-A, PR-B, and PR-D through PR-H from the refreshed preflight
  plan to restore a green pytest suite.
- [ ] Capture fresh verify and coverage logs once the suite passes and update
  release documentation.
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
