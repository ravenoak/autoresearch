# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. Running
`uv run python scripts/check_env.py` continues to confirm the expected
toolchain once the `dev-minimal` and `test` extras are synced, and sourcing the
PATH helper emitted by `./scripts/setup.sh --print-path` makes `task
--version` report Go Task 3.45.4 immediately. 【582859†L1-L25】【a129ab†L1-L8】
`eval "$(./scripts/setup.sh --print-path)"` now suffices to expose the CLI in a
fresh shell. 【5a32ba†L1-L3】 The storage suite that previously aborted now
completes: `uv run --extra test pytest
tests/unit/test_storage_manager_concurrency.py -q` passes, and the broader
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` run finishes
with 135 passed, 2 skipped, 1 xfailed, and 1 xpassed tests.
【b8e216†L1-L3】【babc25†L1-L3】 The xpass comes from
`tests/unit/test_storage_errors.py::test_setup_rdf_store_error`, so the stale
xfail marker needs to be removed to keep storage error handling covered.
【9da781†L1-L3】 Distributed coordination and VSS loader checks remain green,
and `uv run --extra docs mkdocs build` still succeeds without navigation
warnings. 【344912†L1-L2】【d180a4†L1-L2】【b1509d†L1-L2】 The release checklist now
depends on cleaning up the xpass, re-running `task verify` to confirm the
resource tracker fix, and refreshing coverage before we can tag 0.1.0a1.

## Dependencies
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)
- [rerun-task-coverage-after-storage-fix](rerun-task-coverage-after-storage-fix.md)
- [remove-stale-xfail-for-rdf-store-error](remove-stale-xfail-for-rdf-store-error.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is
  updated.
- `task docs` (or `uv run --extra docs mkdocs build`) completes after docs
  extras sync.
- Workflows remain manual or dispatch-only.

## Status
Open
