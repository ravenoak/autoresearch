# Correct token budget convergence logic

## Context
`test_suggest_token_budget_converges` expected a budget of 60 but computed
30, suggesting the convergence algorithm or test parameters need adjustment.

## Acceptance Criteria
- Identify discrepancy between expected and computed budgets.
- Fix algorithm or test to match desired behavior.
- Add property-based tests for boundary cases.

## Status
Open

