# Correct token budget history logic

## Context
Unit tests `tests/unit/test_token_budget.py::test_budget_adaptive_history` and
`tests/unit/test_token_usage.py::test_budget_considers_agent_history` expect
adaptive budgets to incorporate per-agent usage. Current behavior returns
incorrect values, such as 16 instead of 17 and 33 instead of 17.

## Acceptance Criteria
- Adaptive budget calculations account for historical per-agent token usage.
- Regression tests cover the scenarios from the failing unit tests.
- Documentation explains the adaptive budget formula.

## Status
Open
