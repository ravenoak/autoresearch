# Token Budget Adaptation

The orchestrator adjusts its token allowance using
`suggest_token_budget` from
[`orchestration.metrics`](../../src/autoresearch/orchestration/metrics.py).
Let `u_t` denote tokens consumed in cycle `t` and `\bar{u}_t` the mean
usage across the last ten **non-zero** cycles. For each agent `i`, let
`a_{i,t}` be the tokens it used in cycle `t` and `\bar{a}_{i,t}` the
mean across its last ten cycles, **including zeros** when the agent is
idle. Define `a_t = \max_i a_{i,t}` and `\bar{a}_t = \max_i \bar{a}_{i,t}`.
With margin `m`, the update is

\[
b_{t+1} = \left\lceil \max(u_t, \bar{u}_t, a_t, \bar{a}_t) (1 + m) \right\rceil.
\]

Negative margins are clamped to zero to avoid suggesting budgets below
observed usage. The implementation subtracts a tiny epsilon before the
ceiling to prevent floating-point drift from inflating the result.

When the new target differs from the current budget the algorithm
immediately adjusts. If no usage has ever been recorded, the budget is
left unchanged. Ten consecutive zero-usage samples after activity shrink
the budget to a minimum of one token.

## Worked Example

Consider two agents, ``A`` and ``B``, with margin ``m = 0.1``:

1. **Cycle 1** – ``A`` uses five tokens. Candidates: ``u_1 = 5``,
   ``\bar{u}_1 = 5``, ``a_1 = 5`` and ``\bar{a}_1 = 5``. The budget is
   ``ceil(5 \times 1.1) = 6``.
2. **Cycle 2** – ``B`` uses thirty tokens while ``A`` is idle, so its
   history records a zero. ``\bar{a}_{A,2} = (5 + 0) / 2 = 2.5`` and
   ``\bar{a}_{B,2} = 30``. Candidates become ``u_2 = 30``,
   ``\bar{u}_2 = 17.5``, ``a_2 = 30`` and ``\bar{a}_2 = 30``. The budget
   rises to ``ceil(30 \times 1.1) = 33``.
3. **Cycle 3** – ``A`` again uses five tokens. ``B`` contributes zero so
   ``\bar{a}_{B,3} = (30 + 0) / 2 = 15``. The candidates are now
   ``u_3 = 5``, ``\bar{u}_3 = 13.3``, ``a_3 = 5`` and ``\bar{a}_3 = 15``.
   The budget drops to ``ceil(15 \times 1.1) = 17``.

This illustrates how an agent's past activity influences future budgets
even when another agent was responsible for a prior spike.

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
