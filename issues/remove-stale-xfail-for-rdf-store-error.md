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

## Dependencies
- None

## Acceptance Criteria
- The xfail marker is removed (or updated to strict mode with a documented
  rationale) from `tests/unit/test_storage_errors.py::test_setup_rdf_store_error`.
- `uv run --extra test pytest tests/unit/test_storage_errors.py::test_setup_rdf_store_error -q`
  passes without reporting an xpass.
- `uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` completes
  without unexpected xpasses and the updated behavior is recorded in STATUS.md
  and TASK_PROGRESS.md.

## Status
Open
