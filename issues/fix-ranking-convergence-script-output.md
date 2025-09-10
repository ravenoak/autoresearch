# Fix ranking convergence script output

## Context
`tests/integration/test_search_ranking_convergence.py::test_ranking_convergence_script`
fails because the script prints `mean convergence step: 1.0` without the
expected `converged in` text.

## Dependencies
None.

## Acceptance Criteria
- `scripts/ranking_convergence.py` reports convergence with "converged in" messaging.
- `tests/integration/test_search_ranking_convergence.py::test_ranking_convergence_script` passes.

## Status
Open
