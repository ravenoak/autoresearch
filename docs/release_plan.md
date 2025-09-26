# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
ROADMAP.md for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **September 24, 2025** and
reflects that the codebase currently sits at the **unreleased 0.1.0a1** version
defined in `autoresearch.__version__`. The project targets **0.1.0a1** for
**September 15, 2026** and **0.1.0** for **October 1, 2026**. See
STATUS.md, ROADMAP.md, and CHANGELOG.md for aligned progress. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Status

`uv run task verify` succeeded on **September 25, 2025 at 02:27:17 Z**
after we normalized BM25 scores, remapped parallel aggregator payloads into
claim-friendly maps, and hardened the numpy stub to generate deterministic
arrays. The log at
[baseline/logs/task-verify-20250925T022717Z.log][verify-log-pass]
shows the storage eviction, distributed executor, and VSS-enabled search
parametrisations passing in sequence, reflecting the updates in
[src/autoresearch/search/core.py][bm25-normalization],
[src/autoresearch/orchestration/parallel.py][parallel-claims],
and [tests/stubs/numpy.py][numpy-stub-deterministic].

A targeted coverage rerun at **September 25, 2025 at 23:30:24 Z** exercised the
previously blocking suites with the same fixes and recorded a clean pass in the
[targeted coverage log][targeted-coverage-log].
The focused log keeps the coverage evidence manageable while we line up the
full sweep on refreshed CI runners.

Broader integration and performance coverage remains outstanding, but the
release gate now has reproducible verification and targeted coverage evidence
for the regressions that halted the prior alpha sweep.

[verify-log-pass]:
  ../baseline/logs/task-verify-20250925T022717Z.log
[bm25-normalization]:
  ../src/autoresearch/search/core.py#L705-L760
[parallel-claims]:
  ../src/autoresearch/orchestration/parallel.py#L145-L182
[numpy-stub-deterministic]:
  ../tests/stubs/numpy.py#L12-L81
[targeted-coverage-log]:
  ../baseline/logs/task-coverage-20250925T233024Z-targeted.log

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

- [ ] Source the Task PATH helper or invoke release commands through
  `uv run task …` as described in
  [releasing.md](releasing.md#preparing-the-environment) so the CLI is
  available in fresh shells. Reference the [STATUS.md][status-cli] log when
  that guidance changes.

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
- [x] `uv run --extra build python -m build` succeeded out of band and archived
  `baseline/logs/python-build-20250925T001554Z.log`, so packaging is ready to
  resume once verify and coverage pass.
  【F:baseline/logs/python-build-20250925T001554Z.log†L1-L14】
- [ ] Dry-run publish to TestPyPI remains on hold per the release plan until
  the verify and coverage regressions are cleared.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L448-L485】
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

