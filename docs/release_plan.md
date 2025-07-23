# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md).

The project kicked off in **May 2025** (see the initial commit dated `2025-05-18`).
This schedule was last updated on **July 23, 2025** and reflects the fact that
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

The **0.1.0** release was originally aimed for **July 20, 2025**. Ongoing work has
shifted the timeline. The milestone is now planned for **August 15, 2025**.

The following tasks remain before publishing **0.1.0**:

- Run the full unit, integration and behavior test suites across all supported storage and message backends.
- Complete API reference and user guides, questioning assumptions and addressing counterarguments.
- Ensure packaging metadata is accurate and verify `poetry build` and `scripts/publish_dev.py` operate correctly.
- Assemble release notes and finalize README instructions.

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test suite.
4. **Publish** – follow the workflow in `deployment.md`: bump the version, run tests, publish to TestPyPI using `./scripts/publish_dev.py`, then release to PyPI with `poetry publish --build`.

Each milestone may include additional patch releases for critical fixes.
