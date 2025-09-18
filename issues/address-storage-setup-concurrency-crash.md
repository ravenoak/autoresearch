# Address storage setup concurrency crash

## Context
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` now aborts
with a segmentation fault in
`tests/unit/test_storage_manager_concurrency.py::test_setup_thread_safe`, even
though the under-budget eviction regression is fixed and
`uv run --extra test pytest tests/unit/test_storage_eviction_sim.py -q` passes.
【0fcfb0†L1-L74】【3c1010†L1-L2】 Running the concurrency test directly reproduces
an abort, indicating that the threaded `StorageManager.setup` path is still
unsafe. 【2e8cf7†L1-L48】【F:src/autoresearch/storage.py†L381-L427】 The crash
prevents `task verify` and `task coverage` from running to completion, so we
need to restore deterministic, thread-safe setup semantics before release.

## Dependencies
- None

## Acceptance Criteria
- `uv run --extra test pytest tests/unit/test_storage_manager_concurrency.py -q`
  completes without aborting or crashing.
- `uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` finishes
  without segmentation faults.
- Documentation such as `STATUS.md` and `TASK_PROGRESS.md` records the fix and
  links to the validating test runs.

## Status
Open
