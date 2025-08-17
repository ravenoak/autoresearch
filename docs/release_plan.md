# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**. Dates are aspirational and may shift as development progresses. The publishing workflow follows the steps in [deployment.md](deployment.md).

The project kicked off in **May 2025** (see the initial commit dated `2025-05-18`).
This schedule was last updated on **August 24, 2025** and reflects the fact that
the codebase currently sits at the **unreleased 0.1.0a1** version defined in
`autoresearch.__version__`. Phase 2 testing tasks remain incomplete:
`uv run flake8 src tests` fails in
`src/autoresearch/orchestration/metrics.py:102:1` (E303), `uv run mypy src`
reports missing attributes in `src/autoresearch/search/core.py`, and `uv run
pytest -q` fails in
`tests/unit/test_cache.py::test_search_uses_cache`,
`tests/unit/test_cache.py::test_cache_is_backend_specific`,
`tests/unit/test_failure_scenarios.py::test_external_lookup_network_failure`,
`tests/unit/test_main_monitor_commands.py::test_serve_a2a_command_keyboard_interrupt`,
and `tests/unit/test_metrics.py::test_metrics_collection_and_endpoint`, so
coverage is not generated and integration and behavior suites are skipped.
Phase 3 (stabilization/testing/documentation) and Phase 4 activities remain
planned.

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| **0.1.0-alpha.1** | 2025-11-15 | Alpha preview to gather feedback while testing settles ([resolve-current-test-failures](../issues/resolve-current-test-failures.md)) |
| **0.1.0** | 2026-03-01 | Finalize packaging, docs and CI checks with tests passing ([resolve-current-test-failures](../issues/resolve-current-test-failures.md), [update-release-documentation](../issues/update-release-documentation.md)) |
| **0.1.1** | 2026-05-15 | Bug fixes and documentation updates |
| **0.2.0** | 2026-08-01 | API stabilization, configuration hot-reload, improved search backends |
| **0.3.0** | 2026-10-15 | Distributed execution support, monitoring utilities |
| **1.0.0** | 2027-01-15 | Full feature set, performance tuning and stable interfaces |

The project originally targeted **0.1.0** for **July 20, 2025**, but the
schedule slipped. To gather early feedback, an alpha **0.1.0-alpha.1**
release is scheduled for **November 15, 2025**. The final **0.1.0** milestone is
now set for **March 1, 2026** while packaging tasks are resolved.

The following tasks remain before publishing **0.1.0**:

- [ ] Resolve flake8 errors and failing tests ([resolve-current-test-failures](../issues/resolve-current-test-failures.md)); `uv run flake8 src tests`, `uv run mypy src`, and `uv run pytest -q` currently fail.
- [ ] Install optional dependencies with `uv pip install -e '.[full,parsers,git,llm,dev]'` so the full unit, integration and behavior suites run successfully.
- [ ] Ensure new dependency pins are reflected in the lock file and docs. `slowapi` is locked to **0.1.9** and `fastapi` must be **0.115** or newer.
- [ ] Verify `python -m build` and `scripts/publish_dev.py` create valid packages across platforms.
- [ ] Assemble final release notes and confirm README instructions.
- [ ] Keep release documentation synchronized across project files ([update-release-documentation](../issues/update-release-documentation.md)).

### Current Blockers

- Failing tests and linter/type-checking errors ([resolve-current-test-failures](../issues/resolve-current-test-failures.md)).
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
