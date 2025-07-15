# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md).

The project kicked off in **May 2025** (see the initial commit dated `2025-05-18`). This schedule was last updated on **July 15, 2025**.

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| **0.1.1** | 2025-07-31 | Bug fixes and documentation updates |
| **0.2.0** | 2025-09-15 | API stabilization, configuration hot-reload, improved search backends |
| **0.3.0** | 2025-11-15 | Distributed execution support, monitoring utilities |
| **1.0.0** | 2026-01-31 | Full feature set, performance tuning and stable interfaces |

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test suite.
4. **Publish** – follow the workflow in `deployment.md`: bump the version, run tests, publish to TestPyPI using `./scripts/publish_dev.py`, then release to PyPI with `poetry publish --build`.

Each milestone may include additional patch releases for critical fixes.
