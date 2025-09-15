# Fix search ranking and extension tests

## Context
Search-related tests continue to fail, but the problem set has narrowed. The
unit ranking suite now passes (`uv run pytest` on 2025-09-15 returns the
expected ordering in
`tests/unit/search/test_ranking_formula.py::test_rank_results_weighted_combination`),
and the integration scenarios in
`tests/integration/test_ranking_formula_consistency.py` now match the values
documented in the specs. Optional extras also load successfully during
`tests/integration/test_optional_extras.py`.

Remaining regressions focus on extension bootstrapping. The unit test
`tests/unit/test_vss_extension_loader.py::TestVSSExtensionLoader::test_verify_extension_failure`
still fails because `VSSExtensionLoader.verify_extension` executes an extra
fallback query, so the mocked cursor records two calls instead of one. The
DuckDB download helpers also mis-handle offline fallbacks and create
non-empty stub files; track those failures separately in
`fix-duckdb-extension-offline-fallback`.

## Dependencies
None.

## Acceptance Criteria
- DuckDB VSS extension loader unit tests pass; offline download fallbacks are
  handled in `fix-duckdb-extension-offline-fallback`.
- Ranking formula tests match documented values.
- Integration tests for extension loading, ranking consistency, and invalid
  weight detection pass.
- Optional extras such as `fastembed` load in test environments.
- Docs reference extension loading and ranking formulae.

## Status
Open
