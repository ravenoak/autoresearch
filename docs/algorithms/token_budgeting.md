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
b_{t+1} = \text{round\_with\_margin}\left(
  \max(u_t, \bar{u}_t, a_t, \bar{a}_t), m
\right).
\]

Negative margins are clamped to zero to avoid suggesting budgets below
observed usage. The implementation uses ``Decimal`` with round-half-up
semantics, so ``.5`` cases round up while fractions such as ``1.1`` round
down to ``1`` without floating-point drift.

When the new target differs from the current budget the algorithm
immediately adjusts. If no usage has ever been recorded, the budget is
left unchanged. Ten consecutive zero-usage samples after activity shrink
the budget to a minimum of one token.

## Worked Example

Consider two agents, ``A`` and ``B``, with margin ``m = 0.1``:

1. **Cycle 1** – ``A`` uses five tokens. Candidates: ``u_1 = 5``,
   ``\bar{u}_1 = 5``, ``a_1 = 5`` and ``\bar{a}_1 = 5``. The budget is
   ``round_with_margin(5, 0.1) = 6``.
2. **Cycle 2** – ``B`` uses thirty tokens while ``A`` is idle, so its
   history records a zero. ``\bar{a}_{A,2} = (5 + 0) / 2 = 2.5`` and
   ``\bar{a}_{B,2} = 30``. Candidates become ``u_2 = 30``,
   ``\bar{u}_2 = 17.5``, ``a_2 = 30`` and ``\bar{a}_2 = 30``. The budget
   rises to ``round_with_margin(30, 0.1) = 33``.
3. **Cycle 3** – ``A`` again uses five tokens. ``B`` contributes zero so
   ``\bar{a}_{B,3} = (30 + 0) / 2 = 15``. The candidates are now
   ``u_3 = 5``, ``\bar{u}_3 = 13.3``, ``a_3 = 5`` and ``\bar{a}_3 = 15``.
   The budget drops to ``round_with_margin(15, 0.1) = 17``.

This illustrates how an agent's past activity influences future budgets
even when another agent was responsible for a prior spike.

## Convergence

Let usage settle at a constant value `u` and define
`b* = round_with_margin(u, m)`. Averaging the last ten non-zero samples
blocks isolated spikes from influencing the limit.

### Assumptions

- `m >= 0`.
- There exists `T` such that for all `t >= T` each agent consumes exactly
  `u` tokens per cycle.
- `\bar{u}_t` averages the last ten **non-zero** totals, while every
  `\bar{a}_{i,t}` averages the last ten per-agent totals **including**
  zeros.

### Bounds and derivation

Define `M_t = \max(u_t, \bar{u}_t, a_t, \bar{a}_t)` and
`R(x) = round_with_margin(x, m)`. For `t >= T` the update rule becomes

\[
b_{t+1} = R(M_t).
\]

Let `U = \max_{j < T} u_j`. While history retains a pre-`T` spike,
`u \le M_t \le U`, giving the bounds

\[
R(u) \le b_{t+1} \le R(U).
\]

Each cycle after `T` replaces one pre-`T` value in the running averages.
Hence `M_t` decreases monotonically to `u` and for `t >= T + 10` the
window contains only the constant usage. Substituting `M_t = u` yields

\[
b_{t+1} = R(u) = b*.
\]

Thus convergence occurs within ten cycles of stable usage. Ten
consecutive zero-usage cycles after activity force all candidates to
zero. The implementation floors the suggestion at one token, giving the
fixed point `b_t = 1` in that case.

### Counterexample

The historical monotonicity proof assumed two properties that do not
hold in the implementation:

- Both metric histories contain at least one positive usage sample, so
  the fallback path that returns the existing budget is never taken.
- Rounding behaves like ``ceil`` instead of round-half-up.

Dropping either assumption breaks strict monotonicity. Hypothesis
generated the following counterexample, which now lives as a regression
test:

```python
from autoresearch.orchestration.metrics import OrchestrationMetrics

idle = OrchestrationMetrics()
active = OrchestrationMetrics()
idle.record_tokens("a", 0, 0)
active.record_tokens("a", 1, 0)
print(idle.suggest_token_budget(10))   # -> 10, fallback to current budget
print(active.suggest_token_budget(10)) # -> 1, first positive sample
```

`idle` never marks `_ever_used_tokens`, so its suggestion leaves the
current budget unchanged. The `active` run records a single token and
computes `round_with_margin(1, 0.1) = 1`, shrinking the budget. After a
positive sample has been recorded, subsequent increases remain
monotonic; only the zero-history fallback violates the strict proof
claim.

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
asserts that the limit `round_with_margin(u, m)` is reached for constant
usage and after temporary workload spikes. Simulation tests
[`test_metrics_token_budget_spec.py`][bounds-test] verify the bounds on
intermediate budgets and use Hypothesis to explore edge cases such as
large spikes and near-zero margins. The Hypothesis scenario
`test_convergence_bound_holds` now runs without an `xfail` guard,
ensuring budgets stay within the documented bounds after spikes.

 For details on usage recording and metrics, see the
 [token budget specification](../token_budget_spec.md).

[tb-test]: ../../tests/unit/test_token_budget_convergence.py
[bounds-test]: ../../tests/unit/test_metrics_token_budget_spec.py
