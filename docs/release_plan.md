# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
ROADMAP.md for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **October 4, 2025** and
reflects that the codebase currently sits at the **unreleased 0.1.0a1** version
defined in `autoresearch.__version__`. The project targets **0.1.0a1** for
**September 15, 2026** and **0.1.0** for **October 1, 2026**. See
STATUS.md, ROADMAP.md, and CHANGELOG.md for aligned progress. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Status

The strict typing gate remains green, and the latest release sweeps now reach
the coverage stage. At **2025-10-04 14:44 UTC** `uv run task verify
EXTRAS="nlp ui vss git distributed analysis llm parsers"` prints
`[verify][lint] flake8 passed`, completes strict mypy, and shows both legacy and
VSS parameterisations of `tests/unit/test_core_modules_additional.py::
test_search_stub_backend` succeeding. The run fails later when
`tests/unit/test_failure_scenarios.py::test_external_lookup_fallback` returns an
empty placeholder URL, isolating the remaining PR-C work.
【F:baseline/logs/task-verify-20251004T144057Z.log†L167-L169】【F:baseline/logs/task-verify-20251004T144057Z.log†L555-L782】
Minutes later `uv run task coverage EXTRAS="nlp ui vss git distributed analysis
llm parsers"` halts on the identical fallback assertion, so coverage evidence
remains anchored to the prior 92.4 % run until the deterministic URL fix lands.
【F:baseline/logs/task-coverage-20251004T144436Z.log†L481-L600】
The [v0.1.0a1 preflight readiness plan](v0.1.0a1_preflight_plan.md) therefore
tracks the fallback repair as the final PR-C step before re-running coverage.
【F:docs/v0.1.0a1_preflight_plan.md†L10-L239】

TestPyPI remains paused; the release plan and alpha ticket cite the new logs and
will resume the dry run only after the fallback regression clears.
【F:docs/v0.1.0a1_preflight_plan.md†L10-L239】【F:issues/prepare-first-alpha-release.md†L1-L39】


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
- [ ] Dry-run publish to TestPyPI remains on hold per the release plan until
  the verify and coverage regressions are cleared and the directive to skip the
  publish stage is lifted.
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

