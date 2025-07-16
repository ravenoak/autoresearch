# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md).

The project kicked off in **May 2025** (see the initial commit dated `2025-05-18`).
This schedule was last updated on **July 16, 2025** and reflects the fact that
the codebase currently sits at an **unreleased 0.1.0** version.

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| **0.1.0** | 2025-07-20 | Finalize packaging, docs and CI checks |
| **0.1.1** | 2025-07-31 | Bug fixes and documentation updates |
| **0.2.0** | 2025-09-15 | API stabilization, configuration hot-reload, improved search backends |
| **0.3.0** | 2025-11-15 | Distributed execution support, monitoring utilities |
| **1.0.0** | 2026-01-31 | Full feature set, performance tuning and stable interfaces |

The following tasks remain before publishing **0.1.0**:

- Verify all automated tests pass in CI.
- Review documentation for clarity using a Socratic approach—question each section's assumptions and evidence.
- Conduct a dialectical evaluation of core workflows, addressing potential counterarguments in the docs.
- Ensure packaging metadata is accurate and the publish scripts run without error.

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test suite.
4. **Publish** – follow the workflow in `deployment.md`: bump the version, run tests, publish to TestPyPI using `./scripts/publish_dev.py`, then release to PyPI with `poetry publish --build`.

Each milestone may include additional patch releases for critical fixes.
