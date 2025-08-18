# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md). See the [README](../README.md) for installation details and [ROADMAP](../ROADMAP.md) for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated `2025-05-18`).
This schedule was last updated on **August 18, 2025** and reflects the fact that
the codebase currently sits at the **unreleased 0.1.0a1** version defined in
`autoresearch.__version__`. Phase 3 (stabilization/testing/documentation) and
Phase 4 activities remain planned.

## Test and Coverage Status

Phase 2 testing tasks remain incomplete:

 - `flake8 src tests` passes.
 - `mypy src` passes.
 - `pytest -q` fails during collection due to missing modules such as
   `tomli_w`, `freezegun`, `hypothesis`, and `pytest_bdd`, leaving the
   suite unexecuted.
 - `pytest --cov=src` not yet run due to failing tests.

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| **0.1.0-alpha.1** | 2026-02-15 | Alpha preview to collect feedback while resolving test suite failures ([resolve-current-test-failures](../issues/resolve-current-test-failures.md)) |
| **0.1.0** | 2026-06-01 | Finalize packaging, docs and CI checks with all tests passing ([resolve-current-test-failures](../issues/resolve-current-test-failures.md), [update-release-documentation](../issues/archive/update-release-documentation.md)) |
| **0.1.1** | 2026-08-15 | Bug fixes and documentation updates |
| **0.2.0** | 2026-11-01 | API stabilization, configuration hot-reload, improved search backends |
| **0.3.0** | 2027-01-15 | Distributed execution support, monitoring utilities |
| **1.0.0** | 2027-04-01 | Full feature set, performance tuning and stable interfaces |

The project originally targeted **0.1.0** for **July 20, 2025**, but the
schedule slipped. To gather early feedback, an alpha **0.1.0-alpha.1**
release is scheduled for **February 15, 2026**. The final **0.1.0** milestone is
now set for **June 1, 2026** while packaging tasks are resolved.

The following tasks remain before publishing **0.1.0-alpha.1**:

- [ ] Resolve remaining test failures ([resolve-current-test-failures](../issues/resolve-current-test-failures.md)).
- [ ] Set up the environment with `uv venv && uv sync --all-extras && uv pip install -e '.[full,parsers,git,llm,dev]'` so the full unit, integration and behavior suites run successfully.
- [ ] Ensure new dependency pins are reflected in the lock file and docs. `slowapi` is locked to **0.1.9** and `fastapi` must be **0.115** or newer.
- [ ] Verify `python -m build` and `scripts/publish_dev.py` create valid packages across platforms.
- [ ] Assemble preliminary release notes and confirm README instructions.

### Blockers before 0.1.0-alpha.1

| Blocker | Related Issue |
| ------- | ------------- |
| Test suite failures and missing dependencies | [resolve-current-test-failures](../issues/resolve-current-test-failures.md) |
| Development environment misaligned with Python 3.12 and dev tooling | [align-environment-with-requirements](../issues/align-environment-with-requirements.md) |
| Packaging scripts require configuration | [update-release-documentation](../issues/archive/update-release-documentation.md) |

Resolving these issues will determine the new completion date for **0.1.0**.

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test suite.
4. **Publish** – follow the workflow in `deployment.md`: bump the version, run tests, publish to TestPyPI using `./scripts/publish_dev.py`, then release to PyPI with `twine upload dist/*`.

Each milestone may include additional patch releases for critical fixes.

## CI Checklist

Before tagging **0.1.0**, ensure the following checks pass (after installing optional extras):

- [ ] `uv run flake8 src tests`
- [ ] `uv run mypy src`
- [ ] `uv run pytest -q`
- [ ] `uv run pytest tests/behavior`
- [ ] `task coverage` reports at least **90%** total coverage
