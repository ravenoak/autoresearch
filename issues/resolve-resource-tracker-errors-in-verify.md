# Resolve resource tracker errors in verify

## Context
`task verify` previously exited with multiprocessing resource tracker
`KeyError` messages after unit tests, preventing integration tests and
coverage from completing.

Evaluating `./scripts/setup.sh --print-path` now exposes Go Task 3.45.4 in the
base shell, so `task verify` can run without an extra `uv` wrapper once the
venv PATH helper is loaded. 【c1ab5e†L1-L8】【5a32ba†L1-L3】 Targeted retries of the
distributed coordination property suite and the VSS extension loader tests
still demonstrate clean shutdowns when the `[test]` extras are present.
【344912†L1-L2】【d180a4†L1-L2】 The storage selections that previously crashed now
complete: `uv run --extra test pytest
tests/unit/test_storage_manager_concurrency.py -q` passes, and the broader
`-k "storage"` subset reports 135 passed, 2 skipped, 1 xfailed, and 1 xpassed
tests. 【b8e216†L1-L3】【babc25†L1-L3】 The next step is to rerun `task verify`
directly (ideally with `PYTHONWARNINGS=error::DeprecationWarning`) to confirm
the resource tracker tear-down path is stable now that the storage guard is
fixed.

## Dependencies
- None

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open
