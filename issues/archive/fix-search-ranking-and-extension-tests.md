# Fix search ranking and extension tests

## Context
Search-related tests continued to fail until the search ranking regression
closed on September 17, 2025. Extension bootstrapping now behaves as
expected: `uv run --extra test pytest`
`tests/unit/test_vss_extension_loader.py::TestVSSExtensionLoader::`
`test_load_extension_download_unhandled_exception -q` succeeds and
confirms non-DuckDB errors still propagate. Integration coverage for
ranking consistency (`tests/integration/test_ranking_formula_consistency.py`)
and optional extras (`tests/integration/test_optional_extras.py`) also
passes with the `[test]` extras installed.

`tests/unit/search/test_ranking_formula.py::`
`test_rank_results_weighted_combination` now exercises the default convex
weights documented in `docs/specs/search_ranking.md`, so the validator no
longer raises `ConfigError`. The updated assertions confirm the normalized
weights, semantic dominance, and scoring fallbacks described in the
specification.

## Dependencies
None.

## Acceptance Criteria
- DuckDB VSS extension loader unit tests pass, including
  `test_load_extension_download_unhandled_exception` propagating
  non-DuckDB errors.
- Update `tests/unit/search/test_ranking_formula.py::`
  `test_rank_results_weighted_combination` so it aligns with the validator
  while still exercising non-uniform weights.
- Integration tests for extension loading, ranking consistency, and invalid
  weight detection pass.
- Optional extras such as `fastembed` load in test environments.
- Docs reference extension loading and ranking formulae.

## Status
Archived
