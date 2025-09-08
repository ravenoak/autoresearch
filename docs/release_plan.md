# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
[ROADMAP.md](../ROADMAP.md) for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **September 8, 2025** and
reflects that the codebase currently sits at the **unreleased 0.1.0a1** version
defined in `autoresearch.__version__`. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Status

The dependency pins for `fastapi` (>=0.115.12) and `slowapi` (==0.1.9) are
confirmed in `pyproject.toml` and [installation.md](installation.md). `uv run
flake8 src tests` failed because `flake8` is missing, while `uv run mypy src`
reports success. The `task` CLI is unavailable, so `task verify` and `task
coverage` could not run. A dry-run publish built the package and skipped
upload. Outstanding gaps are tracked in [integration-issue] and [task-issue].
Current test results are mirrored in [../STATUS.md](../STATUS.md).

## Milestones

- **0.1.0a1** (2026-06-15, status: in progress): Alpha preview to collect
  feedback.
- **0.1.0** (2026-07-01, status: planned): Finalized packaging, docs and CI
  checks with all tests passing.
- **0.1.1** (2026-09-15, status: planned): Bug fixes and documentation updates
  ([deliver-bug-fixes-and-docs-update](
  ../issues/archive/deliver-bug-fixes-and-docs-update.md)).
- **0.2.0** (2026-12-01, status: planned): API stabilization, configuration
  hot-reload and improved search backends.
  - [stabilize-api-and-improve-search](
    ../issues/stabilize-api-and-improve-search.md)
    - [streaming-webhook-refinements](
      ../issues/archive/streaming-webhook-refinements.md)
    - [configuration-hot-reload-tests](
      ../issues/archive/configuration-hot-reload-tests.md)
    - [hybrid-search-ranking-benchmarks](
      ../issues/archive/hybrid-search-ranking-benchmarks.md)
- **0.3.0** (2027-03-01, status: planned): Distributed execution support and
  monitoring utilities.
  - [simulate-distributed-orchestrator-performance](
    ../issues/simulate-distributed-orchestrator-performance.md)
- **1.0.0** (2027-06-01, status: planned): Full feature set, performance
  tuning and stable interfaces
  ([reach-stable-performance-and-interfaces](
  ../issues/reach-stable-performance-and-interfaces.md)).

To gather early feedback, an alpha **0.1.0a1** release is targeted for
**June 15, 2026**. The final **0.1.0** milestone is set for **July 1, 2026**
while packaging tasks are resolved.

### Alpha release checklist

- [ ] Confirm STATUS.md and this plan share the same coverage details before
  tagging. CI runs `scripts/update_coverage_docs.py` after `task coverage` to
  sync the value.
- [ ] Ensure Task CLI available ([restore-task-cli-availability](
  ../issues/restore-task-cli-availability.md)).
- [x] Resolve coverage hang ([fix-task-verify-coverage-hang](
  ../issues/archive/fix-task-verify-coverage-hang.md)).

These tasks completed in order: environment bootstrap → packaging verification
→ integration tests → coverage gates → algorithm validation.

### Prerequisites for tagging 0.1.0a1

- `uv run flake8 src tests` failed: command not found.
- `uv run mypy src` passed with no issues.
- `task verify` and `task coverage` could not run because the `task` CLI is
  unavailable.
- Dry-run publish to TestPyPI succeeded using `uv run scripts/publish_dev.py`
  with `--dry-run --repository testpypi`.

The **0.1.0a1** date is re-targeted for **June 15, 2026** and the release
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
syncs with `--python-platform x86_64-manylinux_2_28` to prefer wheels and
skips GPU-only packages unless `EXTRAS="gpu"` is set:

- [ ] `uv run flake8 src tests`
- [ ] `uv run mypy src`
- [ ] `uv run pytest -q`
- [ ] `uv run pytest tests/behavior`
- [ ] `task coverage` reports **100%** for targeted modules; keep docs in sync
  and stay above **90%**
- [ ] [`scripts/update_coverage_docs.py`](../scripts/update_coverage_docs.py)
  syncs docs with `baseline/coverage.xml`

[coverage-gap-issue]: ../issues/archive/resolve-pre-alpha-release-blockers.md
[integration-issue]: ../issues/resolve-current-integration-test-failures.md
[task-issue]: ../issues/restore-task-cli-availability.md
