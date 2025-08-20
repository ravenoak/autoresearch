# Algorithm Validation

This document summarizes evaluations of ranking and token budgeting
heuristics.

## Scoring heuristics

Running `uv run scripts/simulate_scoring.py --query "python"` on the
sample dataset produced a ranking consistent with the formula in
[source_credibility.md](source_credibility.md).

## Token budget heuristics

Property-based tests verify that weighted scores remain normalized and
that `suggest_token_budget` grows monotonically with token usage.
