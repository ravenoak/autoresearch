# Fix search ranking and extension tests

## Context
Search-related tests continue to fail, but the scope narrowed again on
September 17, 2025. Extension bootstrapping now behaves as expected:
`uv run --extra test pytest`
`tests/unit/test_vss_extension_loader.py::TestVSSExtensionLoader::`
`test_load_extension_download_unhandled_exception -q` succeeds and
confirms non-DuckDB errors still propagate. Integration coverage for
ranking consistency (`tests/integration/test_ranking_formula_consistency.py`)
and optional extras (`tests/integration/test_optional_extras.py`) also
passes with the `[test]` extras installed.

The remaining regression lives in
`tests/unit/search/test_ranking_formula.py::`
`test_rank_results_weighted_combination`.
`SearchConfig.normalize_ranking_weights` now raises `ConfigError` when the
supplied weights sum above one, so the test fails after constructing a
`ConfigModel` with weights `(bm25=2.0, semantic=8.0, credibility=0.0)`.
The validator is documented in `docs/specs/config.md`, so the test either
needs to adopt legal weights or assert the new exception. Ranking formula
docs still describe the normalization ladder correctly.

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
Open
