# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md).

The project kicked off in **May 2025** (see the initial commit dated `2025-05-18`).
This schedule was last updated on **July 28, 2025** and reflects the fact that
the codebase currently sits at the **unreleased 0.1.0** version defined in
`autoresearch.__version__`.

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| **0.1.0** | 2025-08-15 | Finalize packaging, docs and CI checks |
| **0.1.1** | 2025-08-31 | Bug fixes and documentation updates |
| **0.2.0** | 2025-10-15 | API stabilization, configuration hot-reload, improved search backends |
| **0.3.0** | 2025-12-15 | Distributed execution support, monitoring utilities |
| **1.0.0** | 2026-03-01 | Full feature set, performance tuning and stable interfaces |

The **0.1.0** release was originally aimed for **July 20, 2025**. After resolving
test failures, recent runs show the full suite passing with coverage just over
**90%**. Packaging checks and documentation polish remain, so the milestone is
tentatively scheduled for **August 15, 2025**; if those final tasks slip, the
date will be updated to **TBD**.

The following tasks remain before publishing **0.1.0**:

- [x] Fix failing unit and behavior tests so CI passes.
- [x] Install optional dependencies with `uv pip install -e '.[full,dev]'` so the full unit, integration and behavior suites run successfully.
- [x] Ensure new dependency pins are reflected in the lock file and docs. `slowapi` is locked to **0.1.9** and `fastapi` must be **0.115** or newer.
- [x] Achieve at least **90%** coverage across all suites.
- Verify `python -m build` and `scripts/publish_dev.py` create valid packages across platforms.
- Assemble final release notes and confirm README instructions.

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test suite.
4. **Publish** – follow the workflow in `deployment.md`: bump the version, run tests, publish to TestPyPI using `./scripts/publish_dev.py`, then release to PyPI with `twine upload dist/*`.

Each milestone may include additional patch releases for critical fixes.

## CI Checklist

Before tagging **0.1.0**, ensure the following checks pass (after installing optional extras):

- [x] `uv run flake8 src tests`
- [x] `uv run mypy src`
- [x] `uv run pytest -q`
- [x] `uv run pytest tests/behavior`
- [x] `task coverage` reports at least **90%** total coverage
