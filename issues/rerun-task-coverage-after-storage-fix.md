# Rerun task coverage after storage teardown fix

## Context
The last recorded coverage run (`uv run task coverage EXTRAS="nlp ui vss git
distributed analysis llm parsers gpu"`) reported 90% line coverage, but the
suite cannot reach coverage today. `uv run --extra test pytest tests/unit -k
"storage" -q --maxfail=1` now fails at
`tests/unit/test_storage_eviction_sim.py::test_under_budget_keeps_nodes`
because `_enforce_ram_budget` trims nodes even when the mocked RAM usage stays
within the budget. 【d7c968†L1-L164】 After syncing the `dev-minimal`, `test`, and
`docs` extras, `uv run python scripts/check_env.py` in a fresh container now
flags the Go Task CLI plus unsynced development and test tooling (e.g., `black`,
`flake8`, `fakeredis`, `hypothesis`) until `task install` or `uv sync` installs
the extras. Both the eviction regression and the tooling gap must be resolved
before we can refresh `baseline/coverage.xml` and publish a new status log.
【cd57a1†L1-L24】【F:docs/status/task-coverage-2025-09-17.md†L1-L28】

## Dependencies
- [fix-storage-eviction-under-budget-regression](fix-storage-eviction-under-budget-regression.md)
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)

## Acceptance Criteria
- `uv run task coverage EXTRAS="nlp ui vss git distributed analysis llm parsers gpu"`
  completes without errors after installing Go Task and the required extras.
- The new coverage report maintains ≥90% line coverage and updates
  `baseline/coverage.xml` plus any derived logs in `docs/status/`.
- STATUS.md and TASK_PROGRESS.md summarize the refreshed coverage results and
  cite the new run.
- `mkdocs build` references the updated coverage log in the docs navigation.

## Status
Open
