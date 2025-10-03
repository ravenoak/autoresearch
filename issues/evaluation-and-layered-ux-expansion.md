# Evaluation and layered ux expansion

## Context
Phase 4 expands the benchmark harness and layered user experience so we can
Phase 4 tracks the same registry clone and semantic fallback protections,
keeping the restored 92.4 % coverage run available for UX regressions
while strict typing work continues. The unit suites cover snapshot
register/update/round-trip behaviour and the encode fallback, ensuring
evaluation exports stay stable when optional dependencies shift.
【F:src/autoresearch/orchestration/state_registry.py†L18-L148】
【F:tests/unit/orchestration/test_state_registry.py†L21-L138】
【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
【F:src/autoresearch/search/core.py†L147-L199】
【F:tests/unit/search/test_query_expansion_convergence.py†L154-L206】

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

Automated strict gating runs via `task mypy-strict` inside the Task CLI and CI
workflow, the deterministic storage resident floor is documented for release
audits, and PR5/PR4 upgrades add reverification badges plus session-graph
exports that the layered UX must surface alongside evaluation telemetry.
【F:Taskfile.yml†L62-L104】【F:.github/workflows/ci.yml†L70-L104】
【F:docs/storage_resident_floor.md†L1-L23】
【F:src/autoresearch/orchestration/reverify.py†L73-L197】
【F:src/autoresearch/search/context.py†L618-L666】

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

## Checklist
- [x] Record the strict typing and coverage prerequisites for Phase 4 in
  `docs/deep_research_upgrade_plan.md`, referencing the **14:55 UTC** strict
  `mypy` log.
- [x] Sync the performance and pseudocode docs with the expanded
  `EvaluationSummary` metrics needed for layered exports.
- [ ] Resume layered UX delivery once
  `baseline/logs/task-verify-20250930T145541Z.log` is green and the 92.4 %
  coverage sweep repeats without regressions.

## Status
In Review
