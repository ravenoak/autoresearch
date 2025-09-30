# Cost aware model routing

## Context
Phase 5 adds role-specific model selection with budget caps so we can reduce
latency and token spend without sacrificing accuracy. We need configurable
budget policies, routing telemetry, and regression tests that demonstrate cost
savings alongside quality guarantees.

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)
- [evaluation-and-layered-ux-expansion](evaluation-and-layered-ux-expansion.md)

## Acceptance Criteria
- Configuration supports per-role model defaults, escalation rules, and budget
  ceilings with operator overrides.
- Routing engine selects the cheapest model that satisfies task requirements
  while logging token usage, latency, and confidence metrics.
- Gate policy and planner can request escalations when cheaper models underperform.
- Evaluation harness captures cost savings and accuracy deltas for routing
  experiments, with thresholds documented in the release plan.
- Documentation updates in `docs/specification.md`, `docs/performance.md`, and
  `docs/deep_research_upgrade_plan.md` cover routing strategy, telemetry fields,
  and tuning guidance.

## Checklist
- [x] Document in `docs/deep_research_upgrade_plan.md` that Phase 5 is gated on
  resolving the **14:55 UTC** strict `mypy` failures and restoring coverage.
- [x] Update `docs/performance.md` and `docs/pseudocode.md` so routing metrics
  include the expanded `EvaluationSummary` fields required for budget tracking.
- [ ] Resume routing work once
  `baseline/logs/task-verify-20250930T145541Z.log` is clear and the 92.4 %
  coverage log is reproducible.

## Status
Open
