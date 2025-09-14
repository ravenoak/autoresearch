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
    - Maintain the last ten non-zero samples for global and per-agent usage.
    - If recent deltas are all zero, return `1` after prior activity or leave
      the budget unchanged.
    - Otherwise set the budget to
      `max(ceil(max(u_t, \bar{u}_t, a_t, \bar{a}_t) * (1 + margin)), 1)`.

## Invariants

- Compressed prompts never exceed the token budget.
- Suggested budgets are integers of at least one token.
- Historical averages only incorporate non-zero usage samples.

## Proof Sketch

Running averages bound the compression threshold, ensuring prompts remain within
budget. Budgets are derived from maxima of recent usage, guaranteeing the
minimum token constraint. Simulation in `token_budget_convergence.py`
demonstrates convergence toward `ceil(u * (1 + margin))` for constant
workloads.

## Simulation Expectations

`token_budget_convergence.py` simulates steady workloads to verify convergence
of suggested budgets. The script records metrics showing budgets approach
`ceil(u * (1 + margin))` and that the minimum budget of one token is enforced
after idle periods.

