# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. As of
2025-09-18 the base shell still lacks the Go Task CLI—`task --version` returns
"command not found"—but `uv run python scripts/check_env.py` now reports the
expected toolchain once the `dev-minimal` and `test` extras are synced.
【8a589e†L1-L2】【55fd29†L1-L18】【cb3edc†L1-L10】 Targeted suites confirm the
distributed coordination properties and VSS extension scenarios pass with the
`[test]` extras installed, and `uv run --extra docs mkdocs build` completes
without navigation warnings. 【344912†L1-L2】【d180a4†L1-L2】【b1509d†L1-L2】 The
storage eviction regression is resolved—`uv run --extra test pytest
tests/unit/test_storage_eviction_sim.py -q` now passes—but the broader
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` command
aborts with a segmentation fault in
`tests/unit/test_storage_manager_concurrency.py::test_setup_thread_safe`.
Running that test directly reproduces the crash, so the threaded setup path has
to be hardened before `task verify` and coverage can complete.
【3c1010†L1-L2】【0fcfb0†L1-L74】【2e8cf7†L1-L48】 These gaps block the release
checklist and require targeted fixes before we can tag 0.1.0a1.

## Dependencies
- [address-storage-setup-concurrency-crash](address-storage-setup-concurrency-crash.md)
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)
- [rerun-task-coverage-after-storage-fix](rerun-task-coverage-after-storage-fix.md)

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
