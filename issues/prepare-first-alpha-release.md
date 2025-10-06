# Prepare first alpha release

## Context
As of **October 6, 2025 at 04:53 UTC** `uv run mypy --strict src tests` reports
“Success: no issues found in 794 source files”, verifying the strict gate stays
green after the latest merges.【4fb61a†L1-L2】 A full
`uv run --extra test pytest` sweep at the same timestamp halts during
collection with 19 errors triggered by duplicated imports that precede
`from __future__ import annotations` and missing
`tests/unit/legacy/typing_helpers.py`, `tests/scripts/check_env.py`,
`tests/scripts/distributed_perf_sim.py`, `tests/scripts/download_duckdb_extensions.py`,
and `tests/baseline/evaluation/scheduler_benchmark.json` references in the legacy
harness.【364b98†L1-L60】 These failures prevent the suite from exercising the
orchestrator regressions recorded below. After restoring those fixtures, a
targeted `uv run --extra test pytest tests/unit/legacy -k cache` run now
collects successfully and fails on the known cache assertion, confirming the
imports resolve again.【f1459e†L1-L131】

As of **October 6, 2025 at 04:41 UTC** the merged search, cache, and AUTO-mode
telemetry PRs introduced lint regressions: `uv run task verify` now fails
inside `flake8` with unused imports, duplicate definitions, misplaced
`__future__` imports, and newline violations across behaviour, integration,
and storage suites, preventing mypy and pytest from executing.
【F:baseline/logs/task-verify-20251006T044116Z.log†L1-L124】
The paired coverage sweep begins compiling GPU-heavy extras (for example
`hdbscan==0.8.40`) and was aborted to preserve the evaluation window; the
partial log is archived for the next run after lint repairs.
【F:baseline/logs/task-coverage-20251006T044136Z.log†L1-L8】
The refreshed preflight plan now records **PR-S1**, **PR-S2**, and **PR-R0** as
merged while prioritising lint cleanup and the coverage rerun before TestPyPI
reactivation.【F:docs/v0.1.0a1_preflight_plan.md†L1-L210】 Updated scheduler
baseline data generated on **October 6, 2025 at 15:04 UTC** captures current
throughput floors with provenance metadata for audit reuse.
【F:baseline/evaluation/scheduler_benchmark.json†L1-L15】

As of **October 5, 2025 at 15:43 UTC** reasoning payloads and orchestration
helpers now normalise claims into concrete dictionaries before tests consume
them, and `uv run mypy --strict src tests` logs a clean pass for the alpha
branch.【F:src/autoresearch/orchestration/reasoning_payloads.py†L1-L208】
【F:src/autoresearch/orchestration/parallel.py†L200-L232】
【F:baseline/logs/mypy-strict-20251005T154340Z.log†L1-L2】

As of **October 4, 2025 at 21:04 UTC** the strict typing gate remains green:
`uv run mypy --strict src tests` reports “Success: no issues found in 790
source files”, so the alpha push can continue to rely on strict mode while we
repair the failing pytest surface.【a78415†L1-L2】 The latest
`uv run --extra test pytest` sweep finishes with ten failures across search
stubs, cache determinism, orchestrator telemetry, reasoning answers, and
output formatting fidelity, resetting the release critical path around these
clusters.【53776f†L1-L60】 Targeted property tests highlight how
`OutputFormatter` drops control characters and collapses whitespace, while
search cache tests show backend calls firing despite cached results, further
pinning down the regression scope.【5f96a8†L12-L36】【e865e9†L1-L58】 Focused
reasoning tests now assert that CLI answers stay clean while warning payloads
mirror the metrics telemetry, closing the regression that previously mutated
the summary text.
【F:tests/behavior/steps/reasoning_modes_auto_cli_cycle_steps.py†L685-L723】
【F:src/autoresearch/orchestration/state.py†L132-L206】【34ebc5†L1-L76】
TestPyPI dry runs stay paused per the improvement plan; we will revisit once
the suite is green.

Follow-up work reintroduced canonical URLs and backend labels through
`Search._normalise_backend_documents`, and the stub backend, fallback
return-handles, and failure scenario tests now lock the enriched metadata.
The latest `task verify` sweep reaches those assertions before the known
`test_parallel_merging_is_deterministic` failure returns, so the release gate
remains blocked on orchestrator determinism rather than fallback
placeholders.【F:src/autoresearch/search/core.py†L842-L918】【F:tests/unit/test_core_modules_additional.py†L134-L215】【F:tests/unit/test_failure_scenarios.py†L43-L86】【4c0de7†L1-L120】

## Tasks
- [x] Land **PR-R0** – hydrate AUTO mode claim samples with serialisable
  snapshots and extend coverage so early exits keep claim content.
  【F:src/autoresearch/orchestration/reasoning_payloads.py†L1-L166】
  【F:src/autoresearch/orchestration/parallel.py†L191-L210】
- [x] Land **PR-S1** – restore deterministic search stubs, hybrid ranking
  signatures, and local file fallbacks in line with the updated preflight
  plan.【F:src/autoresearch/search/core.py†L650-L686】【F:src/autoresearch/search/core.py†L1431-L1468】
  【F:tests/unit/legacy/test_cache.py†L503-L608】
- [x] Land **PR-S2** – add namespace-aware cache key helpers, replace the
  function-scoped Hypothesis fixture, and backfill regression coverage so
  cached queries avoid repeated backend calls.【F:tests/unit/legacy/test_cache.py†L503-L608】
  【F:tests/unit/legacy/test_cache.py†L779-L879】【F:tests/unit/legacy/test_cache.py†L883-L1010】
- [ ] Land **PR-O1** – preserve OutputFormatter fidelity for control
  characters and whitespace across JSON and markdown outputs.
- [ ] Land **PR-L0** – reorder `from __future__ import annotations`, drop
  duplicated imports, and rerun `uv run task check` to confirm lint passes
  before pytest collection resumes.
- [x] Land **PR-L1** – redirect legacy imports to the repository `scripts/`
  modules, switch to the shared unit typing helpers, and refresh the scheduler
  benchmark baseline with provenance metadata.【F:tests/unit/legacy/test_check_env_warnings.py†L13-L22】
  【F:tests/unit/legacy/test_distributed_perf_sim_script.py†L10-L52】
  【F:tests/unit/legacy/test_distributed_perf_compare.py†L41-L68】
  【F:tests/unit/legacy/test_download_duckdb_extensions.py†L11-L19】
  【F:tests/unit/legacy/test_scheduling_resource_benchmark.py†L11-L52】
  【F:tests/unit/legacy/test_orchestrator_perf_sim.py†L12-L49】
  【F:tests/unit/legacy/test_additional_coverage.py†L25-L32】
  【F:tests/unit/legacy/test_failure_scenarios.py†L12-L33】
  【F:tests/unit/legacy/test_more_coverage.py†L20-L40】
  【F:baseline/evaluation/scheduler_benchmark.json†L1-L15】
- [x] Land **PR-R1** – relocate reasoning warning banners into structured
  telemetry and update behaviour coverage to assert clean answers.
  【F:src/autoresearch/orchestration/state.py†L132-L206】
  【F:tests/behavior/steps/reasoning_modes_auto_cli_cycle_steps.py†L685-L723】
- [ ] Land **PR-P1** – normalise parallel reasoning merges and recalibrate
  scheduler benchmarks against recorded baselines.
- [ ] Repair lint fallout from PR-S1/S2/R0 so `uv run task verify` reaches
  mypy and pytest again, then capture fresh verify and coverage logs for the
  release dossier.
- [ ] Land **PR-V1** – once lint and collection pass, rerun `task verify` and
  `task coverage` without GPU extras, archive the October logs, and update the
  release dossier before the sign-off review.
- [ ] Schedule and run the release sign-off review after the suite and
  coverage gates return to green.


## Dependencies
- [coordinate-deep-research-enhancement-initiative]
  (coordinate-deep-research-enhancement-initiative.md)
- [adaptive-gate-and-claim-audit-rollout]
  (adaptive-gate-and-claim-audit-rollout.md)
- [deliver-evidence-pipeline-2-0](deliver-evidence-pipeline-2-0.md)
- [planner-coordinator-react-upgrade](planner-coordinator-react-upgrade.md)
- [session-graph-rag-integration](session-graph-rag-integration.md)
- [evaluation-and-layered-ux-expansion](evaluation-and-layered-ux-expansion.md)
- [roll-out-layered-ux-and-model-routing]
  (roll-out-layered-ux-and-model-routing.md)
- [build-truthfulness-evaluation-harness]
  (build-truthfulness-evaluation-harness.md)
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
  and this ticket for auditability, while cross-referencing the
  `task-verify-20251005T012754Z.log` and `task-coverage-20251005T013130Z.log`
  artifacts that demonstrate the fallback fix alongside the earlier failing
  runs.【F:baseline/logs/task-verify-20251005T012754Z.log†L1-L196】【F:baseline/logs/task-coverage-20251005T013130Z.log†L1-L184】
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
