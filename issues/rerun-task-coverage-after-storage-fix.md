# Rerun task coverage after storage teardown fix

## Context
The last recorded coverage run (`uv run task coverage EXTRAS="nlp ui vss git
distributed analysis llm parsers gpu"`) reported 90% line coverage, but the
suite could not reach coverage because the storage selection crashed in
`tests/unit/test_storage_manager_concurrency.py::test_setup_thread_safe`.
`uv run --extra test pytest tests/unit/test_storage_manager_concurrency.py -q`
now passes, and the broader `-k "storage"` suite finishes with 135 passed, 2
skipped, 1 xfailed, and 1 xpassed tests, so the concurrency guard is no longer
the blocker. 【b8e216†L1-L3】【babc25†L1-L3】 The xpass comes from
`tests/unit/test_storage_errors.py::test_setup_rdf_store_error`, so we need to
remove the stale xfail marker before the coverage rerun. 【9da781†L1-L3】 The Go
Task CLI is available as soon as we evaluate `./scripts/setup.sh --print-path`,
so we can invoke `task coverage` once the resource tracker verification passes
and the xfail cleanup lands. 【c1ab5e†L1-L8】【5a32ba†L1-L3】 Refreshing
`baseline/coverage.xml` and the docs log remains blocked on those follow-up
fixes. 【F:docs/status/task-coverage-2025-09-17.md†L1-L28】

## Dependencies
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [remove-stale-xfail-for-rdf-store-error](remove-stale-xfail-for-rdf-store-error.md)

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
