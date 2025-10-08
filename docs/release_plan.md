# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
ROADMAP.md for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **October 6, 2025** and
reflects that the codebase currently sits at the **unreleased 0.1.0a1** version
defined in `autoresearch.__version__`. The project targets **0.1.0a1** for
**September 15, 2026** and **0.1.0** for **October 1, 2026**. See
STATUS.md, ROADMAP.md, and CHANGELOG.md for aligned progress. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Status

The strict typing gate remains green: at **2025-10-07 05:48 UTC**
`uv run mypy --strict src tests` reported “Success: no issues found in 797
source files”, so type coverage is stable while we repair pytest regressions.
【6bfb2b†L1-L1】 A focused
`uv run --extra test pytest tests/unit/legacy/test_relevance_ranking.py -k
external_lookup_uses_cache` run in the same window still fails with
`backend.call_count == 3`, keeping cache determinism as the top regression
before the release sweep can resume.【7821ab†L1031-L1034】 The preflight plan now
prioritises five short PRs—PR-L0 (lint parity), PR-S3 (cache guardrails), PR-V1
(verify/coverage refresh), PR-B1 (behaviour hardening), and PR-E1 (evidence
sync)—to restore end-to-end readiness.【F:docs/v0.1.0a1_preflight_plan.md†L1-L320】

Verify still halts inside `flake8`: at **2025-10-06 04:41 UTC**
`uv run task verify` exits with unused imports, duplicate definitions, misplaced
`__future__` imports, and newline violations across the merged search, cache,
and AUTO-mode telemetry modules. Mypy and pytest do not run until lint is
restored.【F:baseline/logs/task-verify-20251006T044116Z.log†L1-L124】 The paired
`uv run task coverage` attempt at the same timestamp began compiling GPU and
analysis extras (`hdbscan==0.8.40` is the first build) and was aborted to avoid
spending the release window on optional wheels; the partial log is archived for
the follow-up sweep once lint is stable.【F:baseline/logs/task-coverage-20251006T044136Z.log†L1-L8】

On **2025-10-08 at 15:11 UTC** the full `uv run task release:alpha` sweep
advanced through lint, strict typing, spec linting, release metadata checks,
and packaging, then halted during the coverage stage when the concurrent
handling check in `tests/unit/legacy/test_a2a_interface.py` failed its timing
assertion. The transcript and checksum live at
`baseline/logs/release-alpha-dry-run-20251008T151148Z.log` and
`baseline/logs/release-alpha-dry-run-20251008T151148Z.sha256` for follow-up
triage.【F:baseline/logs/release-alpha-dry-run-20251008T151148Z.log†L152-L208】
To confirm the TestPyPI stage still works end-to-end, we separately invoked
`uv run python scripts/publish_dev.py --dry-run` at **15:15 UTC**; the command
built both the sdist and wheel artefacts and recorded the dry-run skip along
with a checksum. The artefacts live under
`baseline/logs/testpypi-dry-run-20251008T151539Z.*` for reuse during the next
release attempt.【F:baseline/logs/testpypi-dry-run-20251008T151539Z.log†L1-L13】
The paired checksum document captures the log digest for auditors.
【F:baseline/logs/testpypi-dry-run-20251008T151539Z.sha256†L1-L1】

The [v0.1.0a1 preflight readiness plan](v0.1.0a1_preflight_plan.md) now marks
PR-S1 (deterministic search stubs), PR-S2 (namespace-aware cache keys), and
PR-R0 (AUTO-mode claim hydration) as complete while promoting lint repair,
legacy fixture restoration (PR-L0/PR-L1), orchestrator clean-up (PR-R2/PR-P1),
and coverage refresh (PR-V1) as the next actions.【F:docs/v0.1.0a1_preflight_plan.md†L1-L210】
The alpha ticket mirrors the updated checklist and references the new logs so
release review can trace the lint regression and aborted coverage run.
【F:issues/prepare-first-alpha-release.md†L1-L64】【F:baseline/logs/task-verify-20251006T044116Z.log†L1-L124】

Distributed metrics still cite the captured baselines under
`baseline/evaluation/`. The orchestrator recovery simulation (50 tasks,
0.01 s latency, 0.2 fail rate) averages 89.36 tasks/s with a 0.13 recovery
ratio, and the scheduler micro-benchmark records 121.74 ops/s for one worker
versus 241.35 ops/s for two workers. These figures continue to back the
throughput gates in the benchmark and scheduler suites.
【F:baseline/evaluation/orchestrator_distributed_sim.json†L1-L8】
【F:baseline/evaluation/scheduler_benchmark.json†L1-L9】


## Milestones

- **0.1.0a1** (2026-09-15, status: in progress): Alpha preview to collect
  feedback.
- **0.1.0** (2026-10-01, status: planned): Finalized packaging, docs and CI
  checks with all tests passing.
- **0.1.1** (2026-12-15, status: planned): Bug fixes and documentation
  updates (deliver-bug-fixes-and-docs-update).
- **0.2.0** (2027-03-01, status: planned): API stabilization, configuration
  hot-reload and improved search backends.
  - stabilize-api-and-improve-search
    - streaming-webhook-refinements
    - configuration-hot-reload-tests
    - hybrid-search-ranking-benchmarks
- **0.3.0** (2027-06-01, status: planned): Distributed execution support and
  monitoring utilities.
  - simulate-distributed-orchestrator-performance
- **1.0.0** (2027-09-01, status: planned): Full feature set, performance
  tuning and stable interfaces
  (reach-stable-performance-and-interfaces).

To gather early feedback, an alpha **0.1.0a1** release is targeted for
**September 15, 2026**. The final **0.1.0** milestone is set for
**October 1, 2026** while packaging tasks are resolved.

### Alpha release checklist

- [x] Confirm STATUS.md and this plan share the same coverage details before
  tagging. CI runs `scripts/update_coverage_docs.py` after `task coverage` to
  sync the value.
- [x] Ensure Task CLI available (restore-task-cli-availability).
- [x] Resolve coverage hang (fix-task-verify-coverage-hang).

These tasks completed in order: environment bootstrap → packaging verification
→ integration tests → coverage gates → algorithm validation.

### Prerequisites for tagging 0.1.0a1

Run `uv run task release:alpha` to execute the full readiness sweep before
tagging a future alpha build. The command installs the dev-minimal, test, and
default optional extras (excluding `gpu`). It then runs lint, type checks, spec
lint, the verify and coverage tasks, packaging builds, metadata checks, and the
TestPyPI dry run. Pass `EXTRAS="gpu"` when GPU wheels are staged.

- [x] Source the Task PATH helper or invoke release commands through
  `uv run task …` as described in
  [releasing.md](releasing.md#preparing-the-environment). `scripts/setup.sh`
  now refreshes `.autoresearch/path.sh` with the Task installation directory,
  so the helper exposes the CLI in new shells without manual edits.
  Reference the [STATUS.md][status-cli] log when that guidance changes.
  【F:scripts/setup.sh†L9-L93】【F:docs/releasing.md†L11-L15】

- [x] `uv run --extra dev-minimal --extra test flake8 src tests` ran as part of
  the sweep before coverage began and the log advanced to the mypy step without
  surfacing lint errors.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L1-L3】
- [x] `uv run --extra dev-minimal --extra test mypy src` reported "Success: no
  issues found in 115 source files" with the a2a interface exclusion still
  applied.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L3-L4】
- [x] `uv run python scripts/lint_specs.py` executed during the sweep to keep
  the monitor and extensions templates aligned.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L5-L5】
- [x] `uv run --extra docs mkdocs build` completed outside the sweep; the new
  log at `baseline/logs/mkdocs-build-20250925T001535Z.log` confirms the docs
  extras compile cleanly while verify remains blocked.
  【F:baseline/logs/mkdocs-build-20250925T001535Z.log†L1-L15】
- [x] `uv run task verify` completed on 2025-09-25 at 02:27:17 Z after the
  BM25 normalization, parallel aggregator payload mapping, and deterministic
  numpy stub fixes cleared the storage eviction and distributed executor
  regressions. A targeted coverage follow-up at 23:30:24 Z replayed the same
  suites to confirm the behaviour while we schedule a full sweep on refreshed
  runners.
  【F:baseline/logs/task-verify-20250925T022717Z.log†L332-L360】
  【F:baseline/logs/task-verify-20250925T022717Z.log†L400-L420】
  【F:baseline/logs/task-coverage-20250925T233024Z-targeted.log†L1-L14】
  【F:src/autoresearch/search/core.py†L705-L760】
  【F:src/autoresearch/orchestration/parallel.py†L145-L182】
  【F:tests/stubs/numpy.py†L12-L81】
- [x] Storage checklist:
  - Document that the deterministic resident node floor stays at `2`
    whenever release configs omit `minimum_deterministic_resident_nodes` so
    reviewers confirm storage stability without extra overrides. See
    [storage_resident_floor.md](storage_resident_floor.md) for the published
    guidance and regression coverage summary.
- [x] Revalidated the DuckDB vector path now emits two search-phase instance
  lookups plus the direct-only pair (four calls total) while the legacy branch
  stays capped at the direct pair. The refreshed
  `tests/unit/test_core_modules_additional.py::test_search_stub_backend`
  snapshots the counts through `vector_search_counts_log`, and the reproduction
  log confirms the deterministic four-event breakdown for the vector flow.
  【F:tests/unit/test_core_modules_additional.py†L18-L379】
  【22e0d1†L1-L11】
- [x] `uv run --extra build python -m build` succeeded out of band and archived
  `baseline/logs/python-build-20250925T001554Z.log`, so packaging is ready to
  resume once verify and coverage pass.
  【F:baseline/logs/python-build-20250925T001554Z.log†L1-L14】
- [x] Dry-run publish to TestPyPI is back online. The
  `release:alpha` invocation on **2025-10-08** still fails during coverage, but
  the standalone `scripts/publish_dev.py --dry-run` run produced fresh artefacts
  and hashes at `baseline/logs/release-alpha-dry-run-20251008T151148Z.*` and
  `baseline/logs/testpypi-dry-run-20251008T151539Z.*`, so maintainers can keep
  the TestPyPI stage enabled while we repair the coverage regression.
  【F:baseline/logs/task-verify-20251005T031512Z.log†L1-L21】
  【F:baseline/logs/task-coverage-20251005T032844Z.log†L1-L24】
  【F:baseline/logs/release-alpha-20250929T000814Z.summary.md†L7-L10】
- [x] Archived
  [issues/archive/retire-stale-xfail-markers-in-unit-suite.md],
  [issues/archive/refresh-token-budget-monotonicity-proof.md], and
  [issues/archive/stage-0-1-0a1-release-artifacts.md] so XPASS promotions,
  heuristics proofs, and packaging logs landed together.
  【F:issues/archive/retire-stale-xfail-markers-in-unit-suite.md†L1-L81】
  【F:issues/archive/refresh-token-budget-monotonicity-proof.md†L1-L74】
  【F:issues/archive/stage-0-1-0a1-release-artifacts.md†L1-L40】
- [x] Archived
  [issues/archive/stabilize-ranking-weight-property.md],
  [issues/archive/restore-external-lookup-search-flow.md],
  [issues/archive/finalize-search-parser-backends.md], and
  [issues/archive/stabilize-storage-eviction-property.md] so the remaining
  XFAIL guards were resolved before tagging.
  【F:issues/archive/stabilize-ranking-weight-property.md†L1-L57】
  【F:issues/archive/restore-external-lookup-search-flow.md†L1-L58】
  【F:issues/archive/finalize-search-parser-backends.md†L1-L51】
  【F:issues/archive/stabilize-storage-eviction-property.md†L1-L53】

The **0.1.0a1** date is re-targeted for **September 15, 2026** and the release
remains in progress until these prerequisites are satisfied.

Completion of these items confirms the alpha baseline for **0.1.0**.

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test
   suite.
4. **Publish** – follow the workflow in `deployment.md`: run
   `task bump-version -- <new-version>`, run tests, publish to TestPyPI using
   `./scripts/publish_dev.py`, then release to PyPI with `twine upload dist/*`.

Each milestone may include additional patch releases for critical fixes.

## Packaging Workflow

1. `task bump-version -- <new-version>`
2. `uv pip install build twine`
3. `uv build`
4. `uv run twine check dist/*`
5. `uv run python scripts/publish_dev.py --dry-run`
6. Set `TWINE_USERNAME` and `TWINE_PASSWORD` then run
   `uv run twine upload --repository testpypi dist/*`
7. After verifying TestPyPI, publish to PyPI with
   `uv run twine upload dist/*`.

## CI Checklist

Before tagging **0.1.0**, ensure the following checks pass. `task verify`
syncs with `--python-platform x86_64-manylinux_2_28` to prefer wheels. It
installs only `dev-minimal` and `test` extras by default; add groups with
`EXTRAS`, e.g. `EXTRAS="nlp ui"` or `EXTRAS="gpu"`:

- [ ] `uv run flake8 src tests`
- [ ] `uv run mypy src`
- [ ] `uv run pytest -q`
- [ ] `uv run pytest tests/behavior`
- [ ] `task coverage` reports **100% coverage** for targeted modules; keep docs
  in sync and stay above **90%**
- [ ] `scripts/update_coverage_docs.py` syncs docs with
  `baseline/coverage.xml`

[status-cli]:
  https://github.com/autoresearch/autoresearch/blob/main/STATUS.md#status

