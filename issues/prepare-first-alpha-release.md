# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. As of
2025-09-17 the Go Task CLI is still absent in a fresh environment, so running
`uv run task check` fails until contributors install Task manually. After
syncing the `dev-minimal` and `test` extras, `uv run python scripts/check_env.py`
now reports only the missing Go Task CLI. 【12a21c†L1-L9】【0525bf†L1-L26】
Targeted test suites continue to pass where helpers exist: the config weight
validator, DuckDB extension fallback, VSS extension loader, ranking
consistency, and optional extras checks all succeed with the `[test]` extras
installed. 【4567c0†L1-L2】【3108ac†L1-L2】【abaaf2†L1-L2】【897640†L1-L3】【d26393†L1-L2】
However, `uv run pytest tests/unit -q` now stops in the monitor metrics suite
because several tests patch `ConfigLoader.load_config` to return bare objects
without a `storage` attribute. The autouse `cleanup_storage` fixture then calls
`storage.teardown(remove_db=True)` during teardown and raises
`AttributeError: 'C' object has no attribute 'storage'`, so the full suite
never reaches the remaining modules. `uv run pytest tests/unit -k "storage" -q
--maxfail=1` reproduces the failure at
`tests/unit/test_monitor_cli.py::test_metrics_skips_storage`. 【d541c6†L1-L58】
`uv run pytest tests/unit -q` therefore reports hundreds of errors rooted in
the same teardown regression. 【35a0a9†L63-L73】 `uv run mkdocs build` still
fails when docs extras are absent. 【fef027†L1-L3】 These gaps block the release
checklist and require targeted fixes before we can draft reliable release
notes.

## Dependencies
- [restore-distributed-coordination-simulation-exports](
  restore-distributed-coordination-simulation-exports.md)
- [resolve-resource-tracker-errors-in-verify](
  resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](
  resolve-deprecation-warnings-in-tests.md)
- [handle-config-loader-patches-in-storage-teardown](
  handle-config-loader-patches-in-storage-teardown.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is
  updated.
- Workflows remain manual or dispatch-only.

## Status
Open
