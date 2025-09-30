# Evaluation and layered ux expansion

## Context
Phase 4 expands the benchmark harness and layered user experience so we can
measure truthfulness improvements and deliver transparent research outputs.
Work includes automating TruthfulQA, FEVER, and HotpotQA sweeps, wiring
telemetry dashboards, and synchronizing CLI/GUI depth controls with per-claim
citations.

The refreshed documentation captures the final-answer audit loop, the
operator acknowledgement controls surfaced in CLI and UI toggles, and the fresh
14:28 UTC `task verify` / 14:30 UTC `task coverage` evidence gathered after the
update. Those logs confirm strict typing and schema blockers remain, so layered
UX reviewers can trace the outstanding work while TestPyPI stays deferred.
【F:docs/release_plan.md†L11-L24】【F:docs/pseudocode.md†L78-L119】
【F:baseline/logs/task-verify-20250930T142820Z.log†L1-L36】
【F:baseline/logs/task-coverage-20250930T143024Z.log†L1-L41】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)
- [session-graph-rag-integration](session-graph-rag-integration.md)

## Acceptance Criteria
- `autoresearch evaluate` command (and Taskfile wrapper) run TruthfulQA, FEVER,
  and HotpotQA subsets, persisting metrics with config signatures.
- Dashboard-ready exports include accuracy, citation coverage, contradiction
  rate, cost, latency, planner depth, and routing deltas.
- Layered output controls (`--depth`, audit table toggles, graph previews) are
  available in CLI and GUI, with consistent defaults documented.
- UX surfaces Socratic follow-ups and per-claim status badges aligned with the
  audit pipeline.
- Documentation updates in `docs/output_formats.md`, `docs/user_guide.md`, and
  `docs/deep_research_upgrade_plan.md` describe the layered UX and evaluation
  workflow.

## Status
In Review
