# Token Budget Specification

This document defines helpers that maintain token usage and compress prompts to
fit within dynamic budgets.

## Overview

The helpers track historical usage to adapt future token allocations. They
either compress an over-budget prompt or recommend a new budget based on recent
activity.

## Algorithms

- `compress_prompt_if_needed`
    - Record the length of each prompt to compute a running average.
    - Adjust the compression threshold when the average exceeds the budget.
    - Return the prompt unchanged when it fits within the adjusted threshold.
    - Otherwise call `llm.token_counting.compress_prompt` to reduce the token
      count to the budget.
- `suggest_token_budget`
    - Track total and per-agent token deltas between calls.
    - Maintain the last ten non-zero samples for global usage and track
      per-agent windows that include zeros to reflect idle cycles.
    - When no positive usage has ever been recorded, return the current
      budget. After activity, ten consecutive zero deltas collapse the budget
      to `1`.
    - Otherwise compute
      `round_with_margin(max(u_t, \bar{u}_t, a_t, \bar{a}_t), margin)`,
      treating negative margins as zero.

## Invariants

- Compressed prompts never exceed the token budget.
- Suggested budgets are integers of at least one token.
- Global usage averages ignore zeros while per-agent averages include them.
- Budgets are piecewise monotonic after the first positive delta and preserve
  the configured budget beforehand.

## Proof Sketch

Running averages bound the compression threshold, ensuring prompts remain
within budget. Budgets derive from recent usage maxima, apply
`round_with_margin`, and clamp negative margins to zero so the suggestion never
lags behind observed demand. The zero-history fallback keeps the configured
budget until a positive delta arrives, after which larger deltas cannot reduce
the recommendation. Simulation in
[token_budget_convergence.py](../../scripts/token_budget_convergence.py)
demonstrates convergence toward `round_with_margin(u, margin)` for constant
workloads.

The zero-history counterexample and the dialectical analysis that favored a
piecewise specification over a heuristic tweak live in
[Token Budget Adaptation](../algorithms/token_budgeting.md#counterexample).

## Simulation Expectations

`token_budget_convergence.py` simulates steady workloads to verify convergence
of suggested budgets. The script records metrics showing budgets approach
`round_with_margin(u, margin)` and that the minimum budget of one token is
enforced after idle periods.

## Traceability

- [`token_budget.py`][impl]
- [`test_metrics_token_budget_spec.py`][tests]
- [`test_heuristic_properties.py`][piecewise-tests]

[impl]: ../../src/autoresearch/token_budget.py
[tests]: ../../tests/unit/legacy/test_metrics_token_budget_spec.py
[piecewise-tests]: ../../tests/unit/legacy/test_heuristic_properties.py

