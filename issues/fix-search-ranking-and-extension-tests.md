# Fix search ranking and extension tests

## Context
Search-related tests continue to fail. The unit test
`tests/unit/search/test_ranking_formula.py::test_rank_results_weighted_combination`
returns `['B', 'A']` instead of `['A', 'B']`. Integration tests also fail:
`tests/integration/test_optional_extras.py::test_vss_extension_loader` cannot
initialize the vector search extension and
`tests/integration/test_ranking_formula_consistency.py::test_convex_combination_matches_docs`
reports mismatched ranking values.
Unit test `tests/unit/test_download_duckdb_extensions.py::test_download_extension_network_fallback`
expects a stubbed extension file but returns a directory path.
On September 14, 2025, `task verify` failed in
`tests/unit/test_relevance_ranking.py::test_rank_results_with_disabled_features`
when ranking returned `0.0` instead of `1.0` with disabled features.

## Dependencies
None.

## Acceptance Criteria
- DuckDB VSS extension loads with fallback when network access is unavailable.
- Ranking formula tests match documented values.
- Integration tests for extension loading and ranking pass.
- Docs reference extension loading and ranking formulae.

## Status
Open
