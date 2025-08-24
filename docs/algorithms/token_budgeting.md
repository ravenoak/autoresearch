# Token Budget Adaptation

The orchestrator adjusts its token allowance using
`suggest_token_budget` from
[`orchestration.metrics`](../../src/autoresearch/orchestration/metrics.py).
Let `u_t` denote tokens consumed in cycle `t` and `\bar{u}_t` the mean
usage across the last ten **non-zero** cycles. For each agent `i`, let
`a_{i,t}` be the tokens it used in cycle `t` and `\bar{a}_{i,t}` the
mean across its last ten non-zero samples. Define `a_t = \max_i a_{i,t}`
and `\bar{a}_t = \max_i \bar{a}_{i,t}`. With margin `m`, the update is

\[
b_{t+1} = \left\lceil \max(u_t, \bar{u}_t, a_t, \bar{a}_t) (1 + m) \right\rceil.
\]

When the new target differs from the current budget the algorithm
immediately adjusts. If no usage has ever been recorded, the budget is
left unchanged. Ten consecutive zero-usage samples after activity shrink
the budget to a minimum of one token.

## Convergence

Let usage settle at a constant value `u` and define
`b* = ceil(u * (1 + m))`. Averaging the last ten non-zero samples blocks
isolated spikes from influencing the limit.

### Proof

Assume there exists `T` such that for all `t >= T`, every agent consumes
`u` tokens. Because `\bar{u}_t` and each `\bar{a}_{i,t}` average the last
ten non-zero values, for `t >= T + 10` these statistics equal `u`. At that
point the update becomes

\[
b_{t+1} = \left\lceil \max(u, u, u, u) (1 + m) \right\rceil = b*.
\]

Since `b*` is a fixed point of the update rule, the sequence `{b_t}` is
constant for `t > T + 10`. Thus `{b_t}` converges to `b*`. Ten consecutive
zero-usage cycles after activity similarly force all candidates to zero,
yielding the fixed point `b_t = 1`.

## Simulation

Run `uv run scripts/token_budget_convergence.py` to observe convergence
for synthetic workloads. As an example,
`uv run scripts/token_budget_convergence.py --steps 5 --usage 50 --margin 0.2`
produces
```
step 1: 60
step 2: 60
step 3: 60
step 4: 60
step 5: 60
final budget: 60
```

The regression test [`test_token_budget_convergence.py`][tb-test]
asserts that the limit `ceil(u * (1 + m))` is reached for constant usage
and after temporary workload spikes. Property-based tests further validate
convergence from arbitrary starting budgets and the minimum budget when
usage is zero.

 For details on usage recording and metrics, see the
 [token budget specification](../token_budget_spec.md).

[tb-test]: ../../tests/unit/test_token_budget_convergence.py
