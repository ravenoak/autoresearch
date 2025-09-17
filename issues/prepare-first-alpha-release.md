# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. As of
2025-09-17 the Go Task CLI is still absent in a fresh environment, so running
`uv run task check` fails until contributors install Task manually. `task
--version` continues to return "command not found", and after syncing the
`dev-minimal` and `test` extras, `uv run python scripts/check_env.py` reports Go
Task as the only missing prerequisite. 【0b96f0†L1-L2】【80552a†L1-L10】 Targeted
test suites confirm that distributed coordination properties, ranking
consistency, and optional extras still pass with the `[test]` extras installed.
【b35e17†L1-L2】【71af25†L1-L2】【b8990e†L1-L2】 However,
`uv run --extra test pytest tests/unit -q` stops in the monitor metrics suite
because the tests patch `ConfigLoader.load_config` to return bare objects
without a `storage` attribute. The autouse `cleanup_storage` fixture calls
`storage.teardown(remove_db=True)` during teardown and raises
`AttributeError: 'C' object has no attribute 'storage'`, so the full suite never
reaches the remaining modules. `uv run --extra test pytest tests/unit -k
"storage" -q --maxfail=1` reproduces the failure at
`tests/unit/test_monitor_cli.py::test_metrics_skips_storage`. The teardown helper
needs a safe fallback when storage settings are missing to unblock coverage.
【529dfa†L1-L57】【4f24c8†L64-L88】【a3c726†L25-L38】【93fac3†L10-L52】 After syncing
the docs extras, `uv run --extra docs mkdocs build` succeeds but warns that
`docs/status/task-coverage-2025-09-17.md` is missing from the navigation, so the
status log must be added to `mkdocs.yml` before release notes are drafted.
【d860f2†L1-L4】【f44ab7†L1-L1】【F:docs/status/task-coverage-2025-09-17.md†L1-L30】
These gaps block the release checklist and require targeted fixes before we can
tag 0.1.0a1.

## Dependencies
- [restore-distributed-coordination-simulation-exports](
  restore-distributed-coordination-simulation-exports.md)
- [resolve-resource-tracker-errors-in-verify](
  resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](
  resolve-deprecation-warnings-in-tests.md)
- [handle-config-loader-patches-in-storage-teardown](
  handle-config-loader-patches-in-storage-teardown.md)
- [add-status-coverage-page-to-docs-nav](
  add-status-coverage-page-to-docs-nav.md)

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
