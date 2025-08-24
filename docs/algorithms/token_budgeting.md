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

When usage stabilizes at `u`, the sequence `{b_t}` converges to
`ceil(u * (1 + m))`. Averaging the last ten non-zero samples prevents
spikes or idle cycles from skewing the estimate.

### Proof of Convergence

Assume there exists `T` such that for all `t \ge T` each agent consumes
exactly `u > 0` tokens. After at most ten cycles the histories examined
by the algorithm contain only `u`, so for all `t \ge T + 9`

```
u_t = u,  \bar{u}_t = u,  a_t = u,  \bar{a}_t = u.
```

Let `b* = ceil(u * (1 + m))`. For all `t \ge T + 9`,

```
b_{t+1} = \lceil \max(u, u, u, u) (1 + m) \rceil = b*.
```

Thus the sequence `{b_t}` becomes constant at `b*` and converges within
ten iterations of usage stabilizing.

## Simulation

Run [`token_budget_convergence.py`](../../scripts/token_budget_convergence.py)
to observe convergence for synthetic workloads. As an example,
`uv run scripts/token_budget_convergence.py --steps 10 --usage 50 --margin 0.2`
produces
```
step 1: 60
step 2: 60
step 3: 60
step 4: 60
step 5: 60
step 6: 60
step 7: 60
step 8: 60
step 9: 60
step 10: 60
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
