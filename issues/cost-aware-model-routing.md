# Cost aware model routing

## Context
Phase 5 adds role-specific model selection with budget caps so we can reduce
latency and token spend without sacrificing accuracy. We need configurable
budget policies, routing telemetry, and regression tests that demonstrate cost
savings alongside quality guarantees.

## Dependencies
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

## Status
Open
