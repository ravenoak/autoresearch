# Token Budget Adaptation

The orchestrator adjusts its token allowance using
`suggest_token_budget` from
[`orchestration.metrics`](../../src/autoresearch/orchestration/metrics.py).
Let `u_t` denote tokens consumed in cycle `t` and `b_t` the budget before
adaptation. With margin `m`, the update is

```
if u_t > b_t * (1 + m):
    b_{t+1} = ceil(u_t * (1 + m))
elif u_t < b_t * (1 - m):
    b_{t+1} = ceil(u_t * (1 + m))
else:
    b_{t+1} = b_t
```

## Convergence

When usage stabilizes at `u`, the sequence `{b_t}` converges to
`ceil(u * (1 + m))`. Both expansion and contraction move `b_t` toward this
value, and once reached, the update returns `b_t` unchanged.

## Simulation

Run `uv run scripts/token_budget_convergence.py` to observe convergence
for synthetic workloads.

For details on usage recording and metrics, see the
[token budget specification](../token_budget_spec.md).
