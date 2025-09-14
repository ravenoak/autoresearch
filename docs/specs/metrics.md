# Metrics

## Overview

Token usage tracking and budget adaptation helpers. See the
[token budgeting algorithm](../algorithms/token_budgeting.md) for update
rules.

## Invariants

- `u_t = \sum_i a_{i,t}`: totals per cycle equal the sum of per-agent tokens.
- Input and output token counters are non-negative and monotonic.
- Suggested budgets `b_t` are integers with `b_t >= 1`.
- Ten consecutive zero-usage cycles after activity force `b_t = 1`.
- Budget suggestions use round-half-up via `round_with_margin`.

## Derivation

Given latest usage `u_t`, its non-zero mean `\bar{u}_t`, the per-agent
maximum `a_t`, and its mean `\bar{a}_t`, the proposed budget is

```
b_{t+1} = round_with_margin(max(u_t, \bar{u}_t, a_t, \bar{a}_t), m)
```

The bounds, convergence proof, and choice of averaging windows are
detailed in [Token Budget Adaptation][tb-derivation].

## Simulation

Running

```
uv run scripts/token_budget_convergence.py --steps 5 --usage 50 --margin 0.2
```

yields

```
step 1: 60
step 2: 60
step 3: 60
step 4: 60
step 5: 60
final budget: 60
```

confirming convergence to `ceil(50 \times 1.2) = 60`.

## Verification

- [tests/unit/test_metrics_token_budget_spec.py][t1] checks expansion,
  shrinkage, rounding, and bounds after spikes.
- [tests/unit/test_token_budget_convergence.py][t2] reproduces the
  simulation above and asserts convergence for constant workloads.

## Traceability

- Modules
  - [src/autoresearch/orchestration/metrics.py][m1]
- Scripts
  - [scripts/token_budget_convergence.py][s1]
- Tests
  - [tests/unit/test_metrics_token_budget_spec.py][t1]
  - [tests/unit/test_token_budget_convergence.py][t2]

[m1]: ../../src/autoresearch/orchestration/metrics.py
[s1]: ../../scripts/token_budget_convergence.py
[t1]: ../../tests/unit/test_metrics_token_budget_spec.py
[t2]: ../../tests/unit/test_token_budget_convergence.py
[tb-derivation]: ../algorithms/token_budgeting.md#bounds-and-derivation

