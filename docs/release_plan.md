# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md).

The project kicked off in **May 2025** (see the initial commit dated `2025-05-18`).
This schedule was last updated on **October 21, 2025** and reflects the fact that
the codebase currently sits at the **unreleased 0.1.0** version defined in
`autoresearch.__version__`.
We are currently in **Phase 2 (testing/documentation)** of the release process.

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| **0.1.0** | 2025-12-20 | Finalize packaging, docs and CI checks |
| **0.1.1** | 2026-02-01 | Bug fixes and documentation updates |
| **0.2.0** | 2026-04-15 | API stabilization, configuration hot-reload, improved search backends |
| **0.3.0** | 2026-07-15 | Distributed execution support, monitoring utilities |
| **1.0.0** | 2026-10-01 | Full feature set, performance tuning and stable interfaces |

The **0.1.0** release was originally aimed for **July 20, 2025**. Many tests
still fail due to configuration errors and overall coverage is below the **90%**
target. Packaging checks and documentation work continue, so the milestone is
now tentatively scheduled for **December 20, 2025**; if these blockers persist,
the date will be updated to **TBD**.

The following tasks remain before publishing **0.1.0**:

- [ ] Fix failing unit and behavior tests so CI passes.
 - [x] Install optional dependencies with `uv pip install -e '.[full,parsers,git,llm,dev]'` so the full unit, integration and behavior suites run successfully.
- [x] Ensure new dependency pins are reflected in the lock file and docs. `slowapi` is locked to **0.1.9** and `fastapi` must be **0.115** or newer.
- [ ] Achieve at least **90%** coverage across all suites.
- [ ] Verify `python -m build` and `scripts/publish_dev.py` create valid packages across platforms.
- Assemble final release notes and confirm README instructions.

### Current Blockers

- Misconfigured test settings cause multiple suites to fail.
- Coverage tooling errors keep overall coverage below the 90% goal.
- Packaging scripts require additional configuration before they run reliably.

Resolving these issues pushes the expected completion of **0.1.0** tasks to
**December 20, 2025**.

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
- [ ] `uv run pytest -q`
- [ ] `uv run pytest tests/behavior`
- [ ] `task coverage` reports at least **90%** total coverage
