# Rerun task coverage after storage teardown fix

## Context
The last recorded coverage run (`uv run task coverage EXTRAS="nlp ui vss git distributed analysis llm parsers gpu"`)
reported 90% line coverage, but storage teardown regressions now prevent
rerunning the task to verify the current baseline.
`uv sync --extra dev-minimal --extra test --extra docs` installs the development, test, and documentation extras, and `uv run python scripts/check_env.py` confirms that only the Go Task CLI remains missing. However, `uv run --extra test pytest tests/unit -k
"storage" -q --maxfail=1` still fails because patched monitor CLI tests trigger `AttributeError: 'C' object has no attribute 'storage'`, so the full unit suite never reaches coverage. We need to rerun `task coverage` once the storage fixture and Go Task availability issues are resolved to refresh `baseline/coverage.xml` and publish a new docs status log.
【ecec62†L1-L24】【5505fc†L1-L27】【1ffd0e†L1-L56】【F:docs/status/task-coverage-2025-09-17.md†L1-L28】

## Dependencies
- [handle-config-loader-patches-in-storage-teardown](handle-config-loader-patches-in-storage-teardown.md)
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
