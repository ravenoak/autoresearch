# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. As of
2025-09-15 the Go Task CLI is absent in a fresh environment, so contributors
must rely on `uv run task ...` or install Task manually before running
automation. After syncing the `dev-minimal`, `test`, and `docs` extras,
`uv run --extra test pytest
tests/unit/test_config_validation_errors.py::test_weights_must_sum_to_one -q`
still fails because overweight ranking vectors no longer raise `ConfigError`,
`uv run --extra test pytest tests/unit/test_download_duckdb_extensions.py -q`
continues to surface `SameFileError` and non-zero offline stubs, and the VSS
extension loader mock expectations still fail due to a second verification
query. Running the unit entry point without extras logs
`PytestConfigWarning: Unknown config option: bdd_features_base_dir`, and
`uv run --extra docs mkdocs build` lists more than forty pages missing from
`nav` alongside broken relative links. These regressions block the release
checklist and require targeted fixes before we can draft reliable release
notes.

## Dependencies
- [fix-search-ranking-and-extension-tests](fix-search-ranking-and-extension-tests.md)
- [fix-config-weight-sum-validation](fix-config-weight-sum-validation.md)
- [fix-duckdb-extension-offline-fallback](fix-duckdb-extension-offline-fallback.md)
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)
- [fix-mkdocs-griffe-warnings](fix-mkdocs-griffe-warnings.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is updated.
- Workflows remain manual or dispatch-only.

## Status
Open
