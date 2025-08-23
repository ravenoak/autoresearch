# Token Budget Adaptation

The orchestrator adjusts its token allowance using
`suggest_token_budget` from
[`orchestration.metrics`](../../src/autoresearch/orchestration/metrics.py).
Let `u_t` denote tokens consumed in cycle `t` and `b_t` the budget before
adaptation. With margin `m`, the update follows the piecewise rule

\[
b_{t+1} =
\begin{cases}
\lceil u_t (1 + m) \rceil & u_t > b_t (1 + m) \\
\lceil u_t (1 + m) \rceil & u_t < b_t (1 - m) \\
b_t & \text{otherwise}
\end{cases}
\]

## Convergence

When usage stabilizes at `u`, the sequence `{b_t}` converges to
`ceil(u * (1 + m))`. The implementation averages the last ten non-zero
usage samples, so transient spikes or idle cycles do not distort the
estimate. Let `b* = ceil(u * (1 + m))`. Deviations shrink linearly because
`|b_{t+1} - b*| \le m |b_t - b*|`, yielding geometric convergence toward
`b*`.

## Simulation

Run `uv run scripts/token_budget_convergence.py` to observe convergence
for synthetic workloads.

[`token_budget_convergence.py`](../../scripts/token_budget_convergence.py)
reports, for example,
`uv run scripts/token_budget_convergence.py --steps 5 --usage 50`
```
step 1: 56
step 2: 56
step 3: 56
step 4: 56
step 5: 56
final budget: 56
```

 The regression test [`test_token_budget_convergence.py`][tb-test]
 asserts that the limit `ceil(u * (1 + m))` is reached for constant usage
 and after temporary workload spikes.

 For details on usage recording and metrics, see the
 [token budget specification](../token_budget_spec.md).

[tb-test]: ../../tests/unit/test_token_budget_convergence.py
