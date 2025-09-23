# Prepare first alpha release

## Context

The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. After
sourcing the PATH helper emitted by `./scripts/setup.sh --print-path`,
`task check` exercises the refreshed extras but stops in `flake8` because
`src/autoresearch/api/routing.py` assigns an unused `e` variable and
`src/autoresearch/search/storage.py` imports `StorageError` without using it.
【153af2†L1-L2】【1dc5f5†L1-L24】【d726d5†L1-L3】 `uv run python scripts/lint_specs.py`
returns successfully and the monitor plus extensions specs include the required
`## Simulation Expectations` heading, so spec lint compliance is restored ahead
of the release tasks.【b7abba†L1-L1】【F:docs/specs/monitor.md†L126-L165】【F:docs/specs/extensions.md†L1-L69】
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` finishes
with 136 passed, 2 skipped, 1 xfailed, and 822 deselected tests, while
`tests/unit/test_storage_errors.py::test_setup_rdf_store_error -q` passes in
3.4 seconds without an xpass. 【f6d3fb†L1-L2】【fba3a6†L1-L2】 `uv run --extra docs
mkdocs build` completes without navigation warnings, so the docs pipeline stays
ready once tests land. 【e808c5†L1-L2】 The release checklist now depends on
cleaning up the new lint regressions, re-running `task verify` to confirm the
resource tracker fix under warnings-as-errors, and refreshing coverage before
tagging v0.1.0a1.

## Dependencies

- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)
- [rerun-task-coverage-after-storage-fix](rerun-task-coverage-after-storage-fix.md)
- [clean-up-flake8-regressions-in-routing-and-search-storage](clean-up-flake8-regressions-in-routing-and-search-storage.md)

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
