# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
ROADMAP.md for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **September 18, 2025** and
reflects that the codebase currently sits at the **unreleased 0.1.0a1** version
defined in `autoresearch.__version__`. The project targets **0.1.0a1** for
**September 15, 2026** and **0.1.0** for **October 1, 2026**. See
STATUS.md, ROADMAP.md, and CHANGELOG.md for aligned progress. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Status

The dependency pins for `fastapi` (>=0.116.1) and `slowapi` (==0.1.9) remain
confirmed in `pyproject.toml` and [installation.md](installation.md), and the
PATH helper saved at `.autoresearch/path.sh` keeps the Go Task CLI available in
fresh shells. `task --version` now succeeds immediately after running
`scripts/setup.sh`. 【11ceea†L1-L8】【c82304†L1-L8】【d609c8†L1-L2】
Running `uv run python scripts/check_env.py` now reports the expected
toolchain—including Go Task 3.45.4, Black, Flake8, and Hypothesis—once the
`dev-minimal` and `test` extras are synced. 【55fd29†L1-L18】【cb3edc†L1-L10】
Targeted storage tests confirm `_enforce_ram_budget` leaves the graph intact
when RAM usage stays under budget, yet
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` aborts
with a segmentation fault in
`tests/unit/test_storage_manager_concurrency.py::test_setup_thread_safe`.
【3c1010†L1-L2】【0fcfb0†L1-L74】 Invoking that concurrency test directly
reproduces the crash, so the threaded setup guard must be hardened before
`task verify` and coverage can complete. 【2e8cf7†L1-L48】 Integration ranking
checks and distributed coordination properties still pass with the `[test]`
extras, and the VSS extension loader suite remains green while deduplicating
offline errors. 【344912†L1-L2】【d180a4†L1-L2】【F:src/autoresearch/extensions.py†L36-L118】
After syncing the docs extras, `uv run --extra docs mkdocs build` completes
without navigation warnings. 【b1509d†L1-L2】【a1ea28†L1-L1】 `task verify` remains
blocked by the storage setup crash, so coverage numbers are still unavailable.
These items are tracked in STATUS.md and the open issues listed there.
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
- `task verify` and `task coverage` executed with Go Task 3.44.1.
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
- [ ] `task coverage` reports **90% coverage** for targeted modules; keep docs
  in sync and stay above **90%**
- [ ] `scripts/update_coverage_docs.py` syncs docs with
  `baseline/coverage.xml`

