# Fix search ranking and extension tests

## Context
Search-related integration tests fail.
`tests/integration/test_optional_extras.py::test_vss_extension_loader` fails to
initialize the vector search extension and
`tests/integration/test_ranking_formula_consistency.py::test_convex_combination_matches_docs`
reports mismatched ranking values.

## Dependencies
None.

## Acceptance Criteria
- DuckDB VSS extension loads with fallback when network access is unavailable.
- Ranking formula tests match documented values.
- Integration tests for extension loading and ranking pass.
- Docs reference extension loading and ranking formulae.

## Status
Open
