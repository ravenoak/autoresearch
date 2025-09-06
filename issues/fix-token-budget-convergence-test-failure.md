# Fix token budget convergence test failure

## Context
`task verify` fails at `tests/unit/test_token_budget_convergence.py::test_convergence_from_any_start`.
The property-based test expects round-half-even to produce a budget of `62` but
the algorithm yields `63`. Rounding logic or test parameters need alignment.

## Dependencies
- None

## Acceptance Criteria
- `test_convergence_from_any_start` passes during `task verify`.
- Token budget algorithm and test agree on rounding behaviour across generated inputs.
- Property-based tests cover edge cases near rounding boundaries.

## Status
Open
