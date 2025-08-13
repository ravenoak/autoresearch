# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md).

The project kicked off in **May 2025** (see the initial commit dated `2025-05-18`).
This schedule was last updated on **August 13, 2025** and reflects the fact that
the codebase currently sits at the **unreleased 0.1.0** version defined in
`autoresearch.__version__`.
Phase 2 testing tasks are complete: integration and behavior tests pass and coverage sits at **92%**, so Phase 3 (stabilization/testing/documentation) and Phase 4 activities remain planned.

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| **0.1.0** | 2025-11-15 | Finalize packaging, docs and CI checks; Phase 2 complete (integration & behavior tests passing, 92% coverage) |
| **0.1.1** | 2026-02-01 | Bug fixes and documentation updates |
| **0.2.0** | 2026-04-15 | API stabilization, configuration hot-reload, improved search backends |
| **0.3.0** | 2026-07-15 | Distributed execution support, monitoring utilities |
| **1.0.0** | 2026-10-01 | Full feature set, performance tuning and stable interfaces |

The **0.1.0** release was originally aimed for **July 20, 2025**, but the
schedule slipped. Tests now pass and total coverage is **92%**. Packaging
checks and documentation work continue, so the milestone remains targeted
for **November 15, 2025** while packaging tasks are completed.

The following tasks remain before publishing **0.1.0**:

- [ ] Confirm Phase 2 results remain stable: integration & behavior tests continue passing with ≥90% coverage.
- [ ] Install optional dependencies with `uv pip install -e '.[full,parsers,git,llm,dev]'` so the full unit, integration and behavior suites run successfully.
- [ ] Ensure new dependency pins are reflected in the lock file and docs. `slowapi` is locked to **0.1.9** and `fastapi` must be **0.115** or newer.
- [ ] Verify `python -m build` and `scripts/publish_dev.py` create valid packages across platforms.
- [ ] Assemble final release notes and confirm README instructions.

### Current Blockers

- Packaging scripts require additional configuration before they run reliably.

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
