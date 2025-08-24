# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
[ROADMAP.md](../ROADMAP.md) for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **August 24, 2025** and
reflects that the codebase currently sits at the **unreleased 0.1.0a1** version
defined in `autoresearch.__version__`. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Status

The dependency pins for `fastapi` (>=0.115.12) and `slowapi` (==0.1.9) are
confirmed in `pyproject.toml` and [installation.md](installation.md).
Current test and coverage results are tracked in
[../STATUS.md](../STATUS.md).

## Milestones

- **0.1.0a1** (2026-04-15, status: in progress): Alpha preview to collect
  feedback
  ([prepare-first-alpha-release](
  ../issues/prepare-first-alpha-release.md)).
- **0.1.0** (2026-07-01, status: planned): Finalize packaging, docs and CI
  checks with all tests passing
  ([finalize-first-public-preview-release](
  ../issues/finalize-first-public-preview-release.md)).
- **0.1.1** (2026-09-15, status: planned): Bug fixes and documentation updates
  ([deliver-bug-fixes-and-docs-update](
  ../issues/deliver-bug-fixes-and-docs-update.md)).
- **0.2.0** (2026-12-01, status: planned): API stabilization, configuration
  hot-reload and improved search backends
  ([stabilize-api-and-improve-search](
  ../issues/stabilize-api-and-improve-search.md)).
- **0.3.0** (2027-03-01, status: planned): Distributed execution support and
  monitoring utilities
  ([support-distributed-execution-and-monitoring](
  ../issues/archive/support-distributed-execution-and-monitoring.md)).
- **1.0.0** (2027-06-01, status: planned): Full feature set, performance
  tuning and stable interfaces
  ([reach-stable-performance-and-interfaces](
  ../issues/reach-stable-performance-and-interfaces.md)).

The project originally targeted **0.1.0** for **July 20, 2025**, but the
schedule slipped. To gather early feedback, an alpha **0.1.0a1** release is
now re-targeted for **April 15, 2026**. The final **0.1.0** milestone is set
for **July 1, 2026** while packaging tasks are resolved.

### Alpha release checklist

- [x] Environment bootstrap documented and installation instructions
  consolidated
  ([document-environment-bootstrap.md](
  ../issues/archive/document-environment-bootstrap.md))
- [x] Packaging verification with DuckDB fallback
  ([verify-packaging-workflow-and-duckdb-fallback.md](
  ../issues/archive/verify-packaging-workflow-and-duckdb-fallback.md))
- [x] Integration test suite passes
  ([stabilize-integration-tests.md](
  ../issues/archive/stabilize-integration-tests.md))
- [ ] Coverage gates target **90%** total coverage; current coverage is
  **24%** (see
  [add-coverage-gates-and-regression-checks.md](
  ../issues/archive/add-coverage-gates-and-regression-checks.md))
- [x] Validate ranking algorithms and agent coordination
  (see
  [validate-ranking-algorithms-and-agent-coordination.md](
  ../issues/archive/validate-ranking-algorithms-and-agent-coordination.md))

These tasks completed in order: environment bootstrap → packaging verification
→ integration tests → coverage gates → algorithm validation.

### Prerequisites for tagging 0.1.0a1

- `flake8` and `mypy` pass, but several unit and integration tests still fail.
- Total coverage is **24%**, short of the **90%** gate.
- TestPyPI upload returns HTTP 403, so packaging needs a retry.

The **0.1.0a1** date is re-targeted for **April 15, 2026** and the release
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

Before tagging **0.1.0**, ensure the following checks pass (after installing
optional extras):

- [ ] `uv run flake8 src tests`
- [ ] `uv run mypy src`
- [ ] `uv run pytest -q`
- [ ] `uv run pytest tests/behavior`
- [ ] `task coverage` currently reports **24%** total coverage; target **90%**

