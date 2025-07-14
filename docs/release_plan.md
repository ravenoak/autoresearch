# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md).

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| **0.1.1** | 2024-07-31 | Bug fixes and documentation updates |
| **0.2.0** | 2024-08-30 | API stabilization, configuration hot-reload, improved search backends |
| **0.3.0** | 2024-09-30 | Distributed execution support, monitoring utilities |
| **1.0.0** | 2024-10-31 | Full feature set, performance tuning and stable interfaces |

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test suite.
4. **Publish** – follow the workflow in `deployment.md`: bump the version, run tests, publish to TestPyPI using `./scripts/publish_dev.py`, then release to PyPI with `poetry publish --build`.

Each milestone may include additional patch releases for critical fixes.
