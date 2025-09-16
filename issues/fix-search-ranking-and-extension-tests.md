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

Remaining regressions focus on extension bootstrapping. Running
`uv run pytest tests/unit/test_vss_extension_loader.py -q` on
2025-09-16 fails in
`TestVSSExtensionLoader.test_load_extension_download_unhandled_exception`
because `VSSExtensionLoader.load_extension` now catches unexpected runtime
errors, logs them, and falls back to stub creation instead of re-raising. The
double `duckdb_extensions()` verification call no longer reproduces, and the
DuckDB download helper suite passes after the offline fallback fixes (see
`issues/archive/fix-duckdb-extension-offline-fallback.md`).

## Dependencies
None.

## Acceptance Criteria
- DuckDB VSS extension loader unit tests pass, including
  `test_load_extension_download_unhandled_exception` propagating
  non-DuckDB errors.
- Ranking formula tests match documented values.
- Integration tests for extension loading, ranking consistency, and invalid
  weight detection pass.
- Optional extras such as `fastembed` load in test environments.
- Docs reference extension loading and ranking formulae.

## Status
Open
