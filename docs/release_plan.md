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

The dependency pins for `fastapi` (>=0.116.1) and `slowapi` (==0.1.9) remain
confirmed in `pyproject.toml` and [installation.md](installation.md). In the
Codex shell `python --version` reports 3.12.10, `uv --version` reports 0.7.22,
and `task --version` still fails, so linting, typing, and test smoke checks run
via `uv` or the PATH helper from `./scripts/setup.sh --print-path`.
`uv run --extra dev-minimal --extra test flake8 src tests` and `uv run --extra
dev-minimal --extra test mypy src` both succeed, and `uv run --extra test pytest
tests/unit -m 'not slow' -rxX` returns 890 passes, 33 skips, eight XFAIL guards,
and five XPASS promotions that align with the open ranking, search, metrics, and
storage tickets. `uv run --extra docs mkdocs build` completes without warnings
after the GPU wheel documentation move, and
[issues/archive/refresh-token-budget-monotonicity-proof.md] plus
[issues/archive/stage-0-1-0a1-release-artifacts.md] capture the proof refresh and
release staging before tagging. Integration and behavior suites succeed with
optional extras skipped, and spec lint remains recovered—`docs/specs/monitor.md`
and `docs/specs/extensions.md` retain the required `## Simulation Expectations`
sections—while coverage artifacts stay in sync with `baseline/coverage.xml`
after the September 23 run documented in `docs/status/task-coverage-2025-09-23.md`.
【c0ed6e†L1-L2】【7b55df†L1-L2】【311dfe†L1-L2】【6c5abf†L1-L1】【16543c†L1-L1】
【5b78c5†L1-L71】【84bbfd†L1-L4】【5b4d9e†L1-L1】
【F:docs/specs/monitor.md†L126-L165】【F:docs/specs/extensions.md†L1-L69】
【F:baseline/coverage.xml†L1-L12】
【F:docs/status/task-coverage-2025-09-23.md†L1-L32】
Revalidated lint, type, spec lint, documentation build, and packaging dry runs
on September 24, 2025 using the current toolchain. `uv run --extra
dev-minimal --extra test flake8 src tests`, `uv run --extra dev-minimal --extra
test mypy src`, and `uv run python scripts/lint_specs.py` returned clean
results.【5bf964†L1-L2】【4db948†L1-L3】【6e0aba†L1-L2】 `uv run --extra docs mkdocs
build` rebuilt the site without warnings.【375bbd†L1-L4】【7349f6†L1-L1】 `uv run
  `uv run --extra build python -m build` and
  `uv run scripts/publish_dev.py --dry-run --repository testpypi` refreshed the
  staged artifacts.【b4608b†L1-L3】【1cbd7f†L1-L3】 The runs are archived in
  `baseline/logs/build-20250924T172531Z.log`.
  【F:baseline/logs/build-20250924T172531Z.log†L1-L13】
  The TestPyPI dry run lives at
  `baseline/logs/publish-dev-20250924T172554Z.log`.
  【F:baseline/logs/publish-dev-20250924T172554Z.log†L1-L14】
The resulting wheel and sdist hashes are tracked below.【064c80†L1-L3】
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

- [x] `uv run --extra dev-minimal --extra test flake8 src tests` passed with no
  issues.【5bf964†L1-L2】
- [x] `uv run --extra dev-minimal --extra test mypy src` reported no type
  errors.【4db948†L1-L3】
- [x] `uv run python scripts/lint_specs.py` kept the monitor and extensions
  templates aligned.【6e0aba†L1-L2】
- [x] `uv run --extra docs mkdocs build` completed without warnings.
  【375bbd†L1-L4】【7349f6†L1-L1】
- [x] `task verify` and `task coverage` executed with Go Task 3.45.4.
  【5d8a01†L1-L2】
- [x] `uv run --extra build python -m build` succeeded using the packaging
  extras.
  - Log: `baseline/logs/build-20250924T172531Z.log`.
    【F:baseline/logs/build-20250924T172531Z.log†L1-L13】
  - SHA256 checksums:
    - `dist/autoresearch-0.1.0a1-py3-none-any.whl` –
      `d223947a04b69e581cebbc2c66c7a6e995eac34cdde4f125775467aea269fbe7`
    - `dist/autoresearch-0.1.0a1.tar.gz` –
      `c33db93fe96270b254692731b948ea5ecc9c69d7b06d22a6f39620382881d762`
      【064c80†L1-L3】
- [x] Dry-run publish to TestPyPI succeeded using
  `uv run scripts/publish_dev.py --dry-run --repository testpypi`.
  - Log: `baseline/logs/publish-dev-20250924T172554Z.log`.
    【F:baseline/logs/publish-dev-20250924T172554Z.log†L1-L14】
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

