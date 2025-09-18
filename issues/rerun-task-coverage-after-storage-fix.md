# Rerun task coverage after storage teardown fix

## Context
The last recorded coverage run (`uv run task coverage EXTRAS="nlp ui vss git
distributed analysis llm parsers gpu"`) reported 90% line coverage, but the
suite cannot reach coverage today. `uv run --extra test pytest tests/unit -k
"storage" -q --maxfail=1` now aborts with a segmentation fault in
`tests/unit/test_storage_manager_concurrency.py::test_setup_thread_safe`
even though the under-budget eviction regression is resolved.
`uv run --extra test pytest tests/unit/test_storage_eviction_sim.py -q`
passes, so the coverage gap is now driven by the threaded setup crash rather
than eviction. 【0fcfb0†L1-L74】【3c1010†L1-L2】 After syncing the `dev-minimal`,
`test`, and `docs` extras, `uv run python scripts/check_env.py` reports the
expected toolchain—including Go Task 3.45.4—when executed via `uv`, but the
base shell still lacks the Task CLI. 【55fd29†L1-L18】【cb3edc†L1-L10】【8a589e†L1-L2】
Both the concurrency crash and the shell-level Task CLI gap must be resolved
before we can refresh `baseline/coverage.xml` and publish a new status log.
【F:docs/status/task-coverage-2025-09-17.md†L1-L28】

## Dependencies
- [address-storage-setup-concurrency-crash](address-storage-setup-concurrency-crash.md)
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
