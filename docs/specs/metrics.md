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

## Monotonicity review (September 2025)

> **Q:** What did the original proof assert about monotonicity?
>
> **A:** It claimed that larger per-cycle usage always yields a larger
> budget because the update took a max and applied a margin via ``ceil``.

> **Q:** Which assumption failed under regression testing?
>
> **A:** Hypothesis reproduced a case where one metrics instance had no
> prior usage. The implementation keeps the current budget in that state,
> while a single-token sample rounds to ``1`` because
> ``round_with_margin`` uses round-half-up semantics. The counterexample
> is now documented in [Token Budget Adaptation][tb-counterexample].

> **Q:** Should the algorithm change to restore strict monotonicity?
>
> **A:** Raising the first positive sample would require special-casing
> small deltas, inviting over-fitting to contrived workloads. The present
> fallback guards cold starts by preserving the configured budget until a
> positive observation arrives, keeping safety aligned with the configured
> margin.

> **Q:** What specification do we adopt?
>
> **A:** We frame the property as *piecewise monotonic*: once any positive
> usage has been observed, larger deltas cannot decrease the suggested
> budget. The regression suite in
> [tests/unit/legacy/test_heuristic_properties.py][tb-tests]
> now covers both the zero-usage fallback and the positive-usage
> monotonicity guarantee.

> **Q:** How do the tests exercise both sides of the dialectic?
>
> **A:** [`test_token_budget_zero_usage_regression`][tb-tests]
> reconstructs the historical counterexample, while the Hypothesis
> [`test_token_budget_monotonicity`][tb-tests] and deterministic
> `test_token_budget_monotonicity_deterministic` confirm the post-usage
> guarantee without the former `xfail` guard.

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

confirming convergence to `round_with_margin(50, 0.2) = 60`.

## Verification

- [tests/unit/legacy/test_metrics_token_budget_spec.py][t1] checks expansion,
  shrinkage, rounding, and bounds after spikes.
- [tests/unit/legacy/test_token_budget_convergence.py][t2] reproduces the
  simulation above and asserts convergence for constant workloads.

## Algorithms

The adaptation algorithm compares recent usage statistics and proposes a
budget that covers observed peaks while remaining integer valued.

## Proof Sketch

Budget suggestions track the maximum of recent usage metrics and apply a
margin. Because the proposal always bounds true usage from above and never
drops below one, convergence follows from monotone sequences.

## Simulation Expectations

Simulations should show the suggested budget approaching the highest
recorded usage scaled by the margin.

## Traceability

- Modules
  - [src/autoresearch/orchestration/metrics.py][m1]
- Scripts
  - [scripts/token_budget_convergence.py][s1]
- Tests
  - [tests/unit/legacy/test_metrics_token_budget_spec.py][t1]
  - [tests/unit/legacy/test_token_budget_convergence.py][t2]
  - [tests/unit/legacy/test_heuristic_properties.py][tb-tests]

[m1]: ../../src/autoresearch/orchestration/metrics.py
[s1]: ../../scripts/token_budget_convergence.py
[t1]: ../../tests/unit/legacy/test_metrics_token_budget_spec.py
[t2]: ../../tests/unit/legacy/test_token_budget_convergence.py
[tb-derivation]: ../algorithms/token_budgeting.md#bounds-and-derivation
[tb-counterexample]: ../algorithms/token_budgeting.md#counterexample
[tb-tests]: ../../tests/unit/legacy/test_heuristic_properties.py

