# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
ROADMAP.md for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **September 19, 2025** and
reflects that the codebase currently sits at the **unreleased 0.1.0a1** version
defined in `autoresearch.__version__`. The project targets **0.1.0a1** for
**September 15, 2026** and **0.1.0** for **October 1, 2026**. See
STATUS.md, ROADMAP.md, and CHANGELOG.md for aligned progress. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Status

The dependency pins for `fastapi` (>=0.116.1) and `slowapi` (==0.1.9) remain
confirmed in `pyproject.toml` and [installation.md](installation.md). Sourcing
`./scripts/setup.sh --print-path` keeps Go Task 3.45.4 on the PATH, and
`task check` still bootstraps the environment with Python 3.12.10 plus the
expected tooling before halting in `flake8` due to the unused `e` assignment
and lingering `StorageError` import tracked in the
clean-up-flake8-regressions-in-routing-and-search-storage issue.
【744f05†L1-L7】【152f28†L1-L2】【48cdde†L1-L25】【910056†L1-L9】【cd3ade†L1-L3】 The
storage suites stay green: `uv run --extra test pytest tests/unit -k "storage"
-q --maxfail=1` finishes with 136 passed, 2 skipped, 822 deselected, and 1
xfailed tests, and the RDF store regression test passes without an xfail
marker. 【714199†L1-L2】【F:issues/clean-up-flake8-regressions-in-routing-and-search-storage.md†L1-L40】
Documentation builds succeed but emit a warning about the testing guidelines
linking to `../wheels/gpu/README.md`, so the fix-testing-guidelines-gpu-link
issue is now part of the release scope.
【9eabf1†L1-L6】【F:docs/testing_guidelines.md†L90-L102】 Spec lint remains
recovered—`docs/specs/monitor.md` and `docs/specs/extensions.md` retain the
required `## Simulation Expectations` sections—so the remaining release work
hinges on fixing the lint regression, confirming the resource tracker teardown,
running the warnings-as-errors sweep, refreshing coverage with optional extras,
and repairing the MkDocs warning noted above.
【F:docs/specs/monitor.md†L126-L165】【F:docs/specs/extensions.md†L1-L69】【F:issues/resolve-resource-tracker-errors-in-verify.md†L1-L33】【F:issues/archive/resolve-deprecation-warnings-in-tests.md†L1-L93】【F:issues/rerun-task-coverage-after-storage-fix.md†L1-L33】【F:issues/fix-testing-guidelines-gpu-link.md†L1-L27】
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

- `uv run flake8 src tests` passed with no issues.
- `uv run mypy src` passed with no issues.
- `uv run python scripts/lint_specs.py` passes with all specs aligned to the
  template (monitor and extensions headings restored).
- `task verify` and `task coverage` executed with Go Task 3.45.4.
  【5d8a01†L1-L2】
- Dry-run publish to TestPyPI succeeded using `uv run scripts/publish_dev.py`
  with `--dry-run --repository testpypi`.

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

