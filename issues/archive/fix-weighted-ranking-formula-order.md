# Fix weighted ranking formula order

## Context
`task verify` fails in `tests/unit/search/test_ranking_formula.py::test_rank_results_weighted_combination`
which expects results sorted by weight but receives them reversed.

## Dependencies
None.

## Acceptance Criteria
- Adjust ranking formula so weighted combinations return highest scores first.
- `tests/unit/search/test_ranking_formula.py::test_rank_results_weighted_combination` passes.

## Status
Archived
