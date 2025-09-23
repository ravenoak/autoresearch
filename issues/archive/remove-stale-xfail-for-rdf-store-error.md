# Remove stale xfail for RDF store error

## Context
`tests/unit/test_storage_errors.py::test_setup_rdf_store_error` is marked with
`pytest.mark.xfail(reason="RDF store path handling differs in CI")`, but the
scenario now passes locally. Running
`uv run --extra test pytest tests/unit/test_storage_errors.py::test_setup_rdf_store_error -q`
reports an xpass, and a fresh run on September 19, 2025 reproduces the xpass in
3.56 seconds. 【cd543d†L1-L1】 The broader
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` selection
finishes with 135 passed, 2 skipped, 1 xfailed, and 1 xpassed tests.
【dbf750†L1-L1】 The lingering xfail hides regressions in the RDF
error path and leaves the release checklist with noisy pytest output. We should
remove the marker, document the environment assumptions, and add a regression
note in STATUS.md so storage coverage reflects the new baseline.

As of September 23, 2025, `uv run --extra test pytest
tests/unit/test_storage_errors.py::test_setup_rdf_store_error -q` passes in
3.4 seconds without reporting an xpass, and the storage selection suite
finishes without additional xpasses, so the stale marker has been removed
and the behavior is reflected in STATUS.md and TASK_PROGRESS.md.
【fba3a6†L1-L2】【f6d3fb†L1-L2】【F:STATUS.md†L1-L16】【F:TASK_PROGRESS.md†L1-L23】

## Dependencies
- None

## Acceptance Criteria
- The xfail marker is removed (or updated to strict mode with a documented
  rationale) from `tests/unit/test_storage_errors.py::test_setup_rdf_store_error`
  and the test passes without reporting an xpass.
- `uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` completes
  without unexpected xpasses and the updated behavior is recorded in STATUS.md
  and TASK_PROGRESS.md.

## Status
Archived
