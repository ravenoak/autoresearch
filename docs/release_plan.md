# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md).

The project kicked off in **May 2025** (see the initial commit dated `2025-05-18`).
This schedule was last updated on **August 16, 2025** and reflects the fact that
the codebase currently sits at the **unreleased 0.1.0a1** version defined in
`autoresearch.__version__`.
Phase 2 testing tasks remain open: `task verify` stops at flake8 due to unused
imports and `uv run pytest` reports failures such as
`tests/unit/test_cli_help.py::test_search_loops_option`, so coverage is not
generated and Phase 3 (stabilization/testing/documentation) and Phase 4 activities
remain planned.

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| **0.1.0-alpha.1** | 2025-11-15 | Alpha preview to gather feedback while fixing tests ([refactor-orchestrator-instance-circuit-breaker](../issues/archive/refactor-orchestrator-instance-circuit-breaker.md), [unit-tests-after-orchestrator-refactor](../issues/unit-tests-after-orchestrator-refactor.md)) |
| **0.1.0** | 2026-03-01 | Finalize packaging, docs and CI checks once tests pass ([refactor-orchestrator-instance-circuit-breaker](../issues/archive/refactor-orchestrator-instance-circuit-breaker.md), [unit-tests-after-orchestrator-refactor](../issues/unit-tests-after-orchestrator-refactor.md)) |
| **0.1.1** | 2026-05-15 | Bug fixes and documentation updates |
| **0.2.0** | 2026-08-01 | API stabilization, configuration hot-reload, improved search backends |
| **0.3.0** | 2026-10-15 | Distributed execution support, monitoring utilities |
| **1.0.0** | 2027-01-15 | Full feature set, performance tuning and stable interfaces |

The project originally targeted **0.1.0** for **July 20, 2025**, but the
schedule slipped. To gather early feedback, an alpha **0.1.0-alpha.1**
release is scheduled for **November 15, 2025** even as `task verify` stops at
flake8 and `uv run pytest` fails in `tests/unit/test_cli_help.py::test_search_loops_option`.
The final **0.1.0** milestone is now set for **March 1, 2026** while these
failures (see [unit-tests-after-orchestrator-refactor](../issues/unit-tests-after-orchestrator-refactor.md)) and packaging tasks
are resolved.

The following tasks remain before publishing **0.1.0**:

- [ ] Resolve flake8 errors and failing tests listed in [unit-tests-after-orchestrator-refactor](../issues/unit-tests-after-orchestrator-refactor.md) and re-run `task coverage` to reach ≥90% total coverage.
- [ ] Install optional dependencies with `uv pip install -e '.[full,parsers,git,llm,dev]'` so the full unit, integration and behavior suites run successfully.
- [ ] Ensure new dependency pins are reflected in the lock file and docs. `slowapi` is locked to **0.1.9** and `fastapi` must be **0.115** or newer.
- [ ] Verify `python -m build` and `scripts/publish_dev.py` create valid packages across platforms.
- [ ] Assemble final release notes and confirm README instructions.

### Current Blockers

- Unit tests failing (for example,
  `tests/unit/test_cli_help.py::test_search_loops_option`); see [unit-tests-after-orchestrator-refactor](../issues/unit-tests-after-orchestrator-refactor.md).
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
