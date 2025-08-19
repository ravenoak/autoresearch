# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses. The publishing
workflow follows the steps in [deployment.md](deployment.md). See the
[README](../README.md) for installation details and [ROADMAP](../ROADMAP.md) for
high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **August 19, 2025** and
reflects the fact that the codebase currently sits at the **unreleased 0.1.0a1**
version defined in `autoresearch.__version__`. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Test and Coverage Status

The dependency pins for `fastapi` (>=0.115.12) and `slowapi` (==0.1.9) are
confirmed in `pyproject.toml` and [installation.md](installation.md).

Phase 2 testing tasks remain incomplete:

- `flake8 src tests` passes.
- `mypy src` currently stalls and needs configuration.
- `pytest -q` runs with all dependencies installed but fails due to search
  scoring bug ([resolve-test-failures]).
- `pytest --cov=src` not yet run because tests fail.

## Milestones

- **0.1.0-alpha.1** (2026-03-01): Alpha preview to collect feedback while
  resolving test suite failures ([resolve-test-failures]).
- **0.1.0** (2026-07-01): Finalize packaging, docs and CI checks with all tests
  passing ([resolve-test-failures]).
- **0.1.1** (2026-09-15): Bug fixes and documentation updates.
- **0.2.0** (2026-12-01): API stabilization, configuration hot-reload,
  improved search backends.
- **0.3.0** (2027-03-01): Distributed execution support, monitoring utilities.
- **1.0.0** (2027-06-01): Full feature set, performance tuning and stable
  interfaces.

The project originally targeted **0.1.0** for **July 20, 2025**, but the
schedule slipped. To gather early feedback, an alpha **0.1.0-alpha.1** release
is scheduled for **March 1, 2026**. The final **0.1.0** milestone is now set for
**July 1, 2026** while packaging tasks are resolved.

The following tasks remain before publishing **0.1.0-alpha.1**:

- [ ] Resolve remaining test failures ([resolve-test-failures]).
  - [ ] Set up the environment with:

    ```
    uv venv && uv sync --all-extras &&
    uv pip install -e '.[full,parsers,git,llm,dev]'
    ```

    Verified flake8 7.3.0, mypy 1.17.1, pytest 8.4.1, pytest-bdd 8.1.0 and
    pydantic 2.11.7; see
    [align-environment-with-requirements](
      ../issues/align-environment-with-requirements.md).
- [x] Ensure new dependency pins are reflected in the lock file and docs.
      `slowapi` is locked to **0.1.9** and `fastapi` is at least **0.115.12**,
      matching `pyproject.toml` and [installation.md](installation.md).
- [x] Verify `uv run python -m build` and
      `uv run python scripts/publish_dev.py --dry-run` create valid packages
      across platforms.
- [ ] Assemble preliminary release notes and confirm README instructions.

### Blockers before 0.1.0-alpha.1

- Test suite failures ([resolve-test-failures])

Resolving these issues will determine the new completion date for **0.1.0**.

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test
   suite.
4. **Publish** – follow the workflow in `deployment.md`: bump the version, run
   tests, publish to TestPyPI using `./scripts/publish_dev.py`, then release to
   PyPI with `twine upload dist/*`.

Each milestone may include additional patch releases for critical fixes.

## Packaging Workflow

1. `uv pip install build twine`
2. `uv run python -m build`
3. `uv run python scripts/publish_dev.py --dry-run`
4. Set `TWINE_USERNAME` and `TWINE_PASSWORD` then run
   `uv run python scripts/publish_dev.py` to upload to TestPyPI.

## CI Checklist

Before tagging **0.1.0**, ensure the following checks pass (after installing
optional extras):

- [ ] `uv run flake8 src tests`
- [ ] `uv run mypy src`
- [ ] `uv run pytest -q`
- [ ] `uv run pytest tests/behavior`
- [ ] `task coverage` reports at least **90%** total coverage

[resolve-test-failures]: ../issues/resolve-current-test-failures.md
