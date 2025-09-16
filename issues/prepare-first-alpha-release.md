# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. As of
2025-09-16 the Go Task CLI is still absent in a fresh environment, so running
`uv run task check` fails until contributors install Task manually. Targeted
unit tests now show that the config weight regression and DuckDB offline
fallback suite have been resolved, but
`tests/unit/test_vss_extension_loader.py::TestVSSExtensionLoader::
test_load_extension_download_unhandled_exception` fails because
`VSSExtensionLoader.load_extension` swallows unexpected runtime errors. API
authentication middleware tests pass, yet running `pytest` without the `[test]`
extra still triggers `PytestConfigWarning: Unknown config option:
bdd_features_base_dir` because `pytest-bdd` is not present. Documentation
tooling also remains unprovisioned; `uv run mkdocs build` cannot start until
the docs extras are synced. These regressions block the release checklist and
require targeted fixes before we can draft reliable release notes.

## Dependencies
- [fix-search-ranking-and-extension-tests](fix-search-ranking-and-extension-tests.md)
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is updated.
- Workflows remain manual or dispatch-only.

## Status
Open
