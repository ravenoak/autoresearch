# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. As of
2025-09-17 the Go Task CLI is still absent in a fresh environment, so running
`uv run task check` fails until contributors install Task manually.
`uv run --extra test pytest`
`tests/unit/test_vss_extension_loader.py::TestVSSExtensionLoader::`
`test_load_extension_download_unhandled_exception -q` now passes and confirms
non-DuckDB exceptions propagate. Targeted config validation, DuckDB download
fallback, and optional extras suites also pass with the `[test]` extras
installed. The remaining unit failure is
`tests/unit/search/test_ranking_formula.py::`
`test_rank_results_weighted_combination`,
which now raises `ConfigError` because the new validator forbids overweight
ranking vectors. Running `uv run mkdocs build` still fails because docs extras
are not present, and the missing Task CLI prevents `task check`/`task verify`
from running end-to-end. These regressions block the release checklist and
require targeted fixes before we can draft reliable release notes.

## Dependencies
- [fix-search-ranking-and-extension-tests](
  fix-search-ranking-and-extension-tests.md)
- [resolve-resource-tracker-errors-in-verify](
  resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](
  resolve-deprecation-warnings-in-tests.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is
  updated.
- Workflows remain manual or dispatch-only.

## Status
Open
