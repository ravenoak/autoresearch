# Prepare first alpha release

## Context
As of **October 8, 2025 at 04:27 UTC** the quick gate remains green:
`uv run task check` passes end-to-end and the log is archived at
`baseline/logs/task-check-20251008T042731Z.log` for release evidence.
【F:baseline/logs/task-check-20251008T042731Z.log†L1-L36】

As of **October 8, 2025 at 03:58 UTC** the lint fallout around misplaced future
imports is cleared: every module called out in the October 6 verify log now
starts with `from __future__ import annotations`, and the redundant pytest
imports added in follow-up merges have been removed.
【F:tests/unit/distributed/test_coordination_properties.py†L1-L13】
【F:tests/unit/monitor/test_metrics_endpoint.py†L1-L15】
【F:tests/unit/storage/test_backup_scheduler.py†L1-L15】
【F:tests/unit/api/test_api_llm.py†L1-L12】【F:tests/unit/api/test_routes.py†L1-L24】
`uv run flake8 tests` now returns cleanly, and the refreshed quick-gate sweep is
archived at `baseline/logs/task-check-20251008T035856Z.log` for release
evidence.【49c894†L1-L2】【F:baseline/logs/task-check-20251008T035856Z.log†L1-L36】
As of **October 7, 2025 at 16:42 UTC** strict typing remains green while pytest
collection still fails. `uv run mypy --strict src tests` reports “Success: no
issues found in 797 source files,” but `uv run --extra test pytest -q` halts on
six modules that import standard-library packages before `from __future__ import
annotations`, yielding SyntaxError and preventing the cache determinism
regression from running.【0aff6f†L1-L1】【2fa019†L1-L65】 We will land PR-L0b to
restore import ordering, add PR-T0 regression guards, and then resume PR-S3.

As of **October 7, 2025 at 04:38 UTC** `uv run task check` now clears `flake8`
and the repo-wide strict sweep before `check_spec_tests.py` fails on missing
doc-to-test anchors, so synchronising the specs with `SPEC_COVERAGE.md` is the
remaining quick-gate blocker.【F:baseline/logs/task-check-20251007T0438Z.log†L1-L165】
Specialised agents coerce `FrozenReasoningStep` payloads into dictionaries
before prompt generation and the orchestration regression extends
`ReasoningCollection` in-place operations, keeping strict typing green while
preserving deterministic reasoning order.
【F:src/autoresearch/agents/specialized/summarizer.py†L9-L78】
【F:src/autoresearch/agents/specialized/critic.py†L9-L101】
【F:src/autoresearch/agents/dialectical/fact_checker.py†L360-L426】
【F:tests/unit/orchestration/test_query_state_features.py†L140-L160】

As of **October 7, 2025 at 16:29 UTC** the strict typing gate regressed:
`uv run mypy --strict src tests` fails on AUTO mode sample hydration because
non-string answers bypass `_freeze_payload` and tests mask immutability probes
with unused ignores.【1fc7a3†L1-L5】 Hardened sample snapshots now coerce
non-string payloads through `_freeze_payload`, and the AUTO mode regression
suite casts retrieved telemetry to `FrozenReasoningStep` tuples so strict mode
observes the runtime immutability checks.【F:src/autoresearch/orchestration/orchestrator.py†L108-L134】
【F:tests/unit/orchestration/test_auto_mode.py†L1-L191】 A follow-up
`uv run mypy --strict src tests` sweep at **16:34 UTC** returns success, and the
targeted AUTO mode regression suite now passes with warnings preserved during
debate escalation.【27806b†L1-L1】【7b397e†L1-L9】 The preflight plan now tracks
short-scope slices PR-L0a (strict gate parity), PR-S3 (cache determinism),
PR-L0b (lint parity), and PR-V1 (evidence refresh) so reviewers can land
iterative improvements without waiting for the full verify gate.

As of **October 7, 2025 at 05:48 UTC** `uv run mypy --strict src tests` still
reports “Success: no issues found in 797 source files,” so the strict gate stays
green while we focus on pytest regressions.【6bfb2b†L1-L1】 A targeted
`uv run --extra test pytest tests/unit/legacy/test_relevance_ranking.py -k
external_lookup_uses_cache` run during the same window continues to fail with
`backend.call_count == 3`, confirming cache determinism remains the top
regression before verify can progress.【7821ab†L1031-L1034】 The updated preflight
plan now sequences PR-L0 (lint parity), PR-S3 (cache guardrails), PR-V1 (verify
and coverage refresh), PR-B1 (behaviour hardening), and PR-E1 (evidence sync) as
short, high-impact slices.

As of **October 7, 2025 at 05:09 UTC** the regenerated spec anchors and docx
stub fallback keep `uv run task check` green end-to-end, with the sweep
archived at `baseline/logs/task-check-20251007T050924Z.log`. The stub now
defers to the in-repo shim when `lxml`'s compiled extension is unavailable in
the manylinux-targeted quick gate, so contributors can run the fast suite on
macOS without compiling libxml2 while CI continues to exercise the real
dependency.【F:tests/stubs/docx.py†L1-L40】

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
- [x] Land **PR-D0** – embed manifest-aligned test references across the specs,
  teach `scripts/check_spec_tests.py` to detect drift, fall back to the docx
  stub when `lxml` wheels are unavailable locally, and capture the green
  `task check` sweep at 05:09 UTC.
  【F:scripts/check_spec_tests.py†L1-L140】【F:tests/stubs/docx.py†L1-L40】
  【F:docs/specs/search.md†L103-L144】【F:baseline/logs/task-check-20251007T050924Z.log†L1-L189】
- [x] Land **PR-L0a** – freeze AUTO mode scout answers, tighten regression
  typing, and capture a green strict sweep for release evidence.
  【F:src/autoresearch/orchestration/orchestrator.py†L108-L134】
  【F:tests/unit/orchestration/test_auto_mode.py†L1-L191】
  【27806b†L1-L1】【7b397e†L1-L9】
- [ ] Land **PR-O1** – preserve OutputFormatter fidelity for control
  characters and whitespace across JSON and markdown outputs.
- [x] Land **PR-L0b** – move `from __future__ import annotations` to the top of
  each failing test module, deduplicate standard-library imports, and rerun
  `uv run task check` to confirm the quick gate is green again.
  【F:tests/unit/distributed/test_coordination_properties.py†L1-L13】
  【F:tests/unit/monitor/test_metrics_endpoint.py†L1-L15】
  【F:tests/unit/storage/test_backup_scheduler.py†L1-L15】
  【49c894†L1-L2】【F:baseline/logs/task-check-20251008T035856Z.log†L1-L36】
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
- [x] Land **PR-A1** – normalise `FrozenReasoningStep` payloads inside
  specialist agents and adjust orchestration regression tests so
  `ReasoningCollection` in-place additions remain type-safe.
- [ ] Land **PR-T0** – add regression coverage that fails when duplicate
  imports precede `from __future__ import annotations`, document the guard, and
  wire it into CI.
- [ ] Repair lint fallout from PR-S1/S2/R0 so `uv run task verify` reaches
  mypy and pytest again, then capture fresh verify and coverage logs for the
  release dossier.
- [ ] Land **PR-L0c** – finish the lint cleanup (unused imports, newline
  violations) that still blocks `task verify` from entering mypy and pytest.
- [ ] Land **PR-V1** – once lint and collection pass, rerun `task verify` and
  `task coverage` without GPU extras, archive the October logs, and update the
  release dossier before the sign-off review.
- [ ] Land **PR-S3** – enforce canonical cache hits so
  `tests/unit/legacy/test_relevance_ranking.py::test_external_lookup_uses_cache`
  observes a single backend call, then expand property coverage for namespace
  churn.
- [ ] Land **PR-B1** – expand behaviour coverage for AUTO-mode cache hits,
  warning banner isolation, and formatter fidelity after PR-S3 lands.
- [ ] Land **PR-E1** – synchronise STATUS.md, TASK_PROGRESS.md,
  CODE_COMPLETE_PLAN.md, the preflight plan, and this ticket with new verify and
  coverage logs after PR-V1 completes.
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
