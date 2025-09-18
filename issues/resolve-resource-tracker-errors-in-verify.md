# Resolve resource tracker errors in verify

## Context
`task verify` previously exited with multiprocessing resource tracker
`KeyError` messages after unit tests, preventing integration tests and
coverage from completing.

On September 18, 2025, the base shell still lacks the Go Task CLI, so
`task --version` continues to report "command not found". Running
`uv run python scripts/check_env.py` now reports the expected toolchain
once the `dev-minimal` and `test` extras are synced, but the Task binary is
available only inside the `uv` environment.
【8a589e†L1-L2】【55fd29†L1-L18】【cb3edc†L1-L10】 Targeted retries of the
distributed coordination property suite and the VSS extension loader tests
still demonstrate clean shutdowns when the `[test]` extras are present.
【344912†L1-L2】【d180a4†L1-L2】 The storage eviction regression has been fixed—
`uv run --extra test pytest tests/unit/test_storage_eviction_sim.py -q` now
passes—but the broader `uv run --extra test pytest tests/unit -k "storage" -q
--maxfail=1` command aborts with a segmentation fault in
`tests/unit/test_storage_manager_concurrency.py::test_setup_thread_safe`.
Running that test directly reproduces the crash, so we still cannot exercise
`task verify` end-to-end to confirm the resource tracker fix until the threaded
setup path is hardened. 【3c1010†L1-L2】【0fcfb0†L1-L74】【2e8cf7†L1-L48】

## Dependencies
- [address-storage-setup-concurrency-crash](
  address-storage-setup-concurrency-crash.md)

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open
