# Algorithm Validation

This document summarizes evaluations of ranking and token budgeting
heuristics.

## Scoring heuristics

Running `uv run scripts/simulate_scoring.py --query "python"` on the
sample dataset produced a ranking consistent with the formula in
[source_credibility.md](source_credibility.md). The script now accepts a
`--weights w_sem w_bm25 w_cred` flag for exploring alternate weight
vectors. Scores that tie after weighting break by source credibility and
document id to ensure deterministic rankings.

## Ranking weights

Grid-searching the weight vector with
[tests/analysis/weight_tuning_analysis.py]
(../../tests/analysis/weight_tuning_analysis.py) converged to `(0.5, 0.3, 0.2)`
with NDCG `1.0`, recorded in
[weight_tuning_metrics.json](../../tests/analysis/weight_tuning_metrics.json).
Property-based tests verify invariants:

- [test_property_bm25_normalization.py][tpbn] keeps BM25 scores in `[0, 1]`.
- [test_property_weight_tuning.py][tpwt] confirms tuned weights sum to one
  and improve NDCG.
- [test_property_weight_convergence.py][tpwc] shows halving the step never
  decreases NDCG.

Let `f(w)` denote the NDCG for weights `w` on the simplex `Δ`. The function is
continuous on compact `Δ`, so the grid `L_h = {w ∈ Δ | w_i ∈ hℕ}` contains a
maximizer `w_h` with `f(w_h) → max_{w∈Δ} f(w)` as `h → 0`. The simulation in
[weight_convergence_metrics.json]
(../../tests/analysis/weight_convergence_metrics.json) shows identical scores
for steps `0.1`, `0.05`, and `0.025`, empirically supporting convergence.

## Ranking stability

Python's sort is stable, so duplicate scores should preserve input order.
Property-based tests, [test_property_ranking_ties.py][tprt], randomize result
sequences and show the ranked output matches the original order. A simulation,
[ranking_tie_analysis.py](../../tests/analysis/ranking_tie_analysis.py), reports
stability `1.0` in
[ranking_tie_metrics.json](../../tests/analysis/ranking_tie_metrics.json).

## Ranking correctness

The simulation [`ranking_correctness_analysis.py`][rca] draws random relevance
scores and confirms that sorting by score yields a non-increasing sequence.
Results show correctness `1.0` in [`ranking_correctness_metrics.json`][rcm].

## Token budget heuristics

Property-based tests verify that weighted scores remain normalized and
that `suggest_token_budget` grows monotonically with token usage. The
suite in [test_heuristic_properties.py][thp] explores random usage
pairs, while [test_property_token_budget_sequence.py][tbseq] checks
longer sequences.

Let `b(u)` denote the suggested budget after consuming `u` tokens. The
function satisfies

```
b(u) = ceil((u + c) * r)
```

with cushion `c > 0` and growth rate `r >= 1`. Addition and
multiplication by non-negative constants preserve ordering, so `b(u)` is
non-decreasing in `u`.

A short simulation confirms the proof:

```
uv run python - <<'PY'
from random import randint
from autoresearch.orchestration.metrics import OrchestrationMetrics
for _ in range(100):
    m = OrchestrationMetrics()
    last = 0
    for _ in range(5):
        u = last + randint(0, 5)
        b = m.suggest_token_budget(u)
        assert b >= last
        last = b
print("monotonic")
PY
```

```
monotonic
```

[thp]: ../../tests/unit/test_heuristic_properties.py
[tbseq]: ../../tests/unit/test_property_token_budget_sequence.py
[tpbn]: ../../tests/unit/test_property_bm25_normalization.py
[tpwt]: ../../tests/unit/test_property_weight_tuning.py
[rca]: ../../tests/analysis/ranking_correctness_analysis.py
[rcm]: ../../tests/analysis/ranking_correctness_metrics.json

## Coordination policies

[tests/analysis/dialectical_cycle_analysis.py]
(../../tests/analysis/dialectical_cycle_analysis.py) runs 100 trials of the
dialectical update with noise `0.1` and stores the final mean and deviation
in
[dialectical_metrics.json](../../tests/analysis/dialectical_metrics.json).
The results match the convergence bound in
[dialectical_coordination.md](dialectical_coordination.md). A property-based
test, [test_property_dialectical_coordination.py][tpdc], validates
convergence to the ground truth in the noiseless case. Let `e^t = b_s^t - g`.
Ignoring noise, the update gives `e^{t+1} = (1 - α/3) e^t`, so after two steps
`|e^t| ≤ (1 - α/3) |g|`. The bound is checked in
[test_property_coordination_stability.py][tpcs]. Another property-based
test, [test_dialectical_cycle_property.py][tdcp], draws pairs of `α` values and
shows that larger fact-checker influence never lowers the final mean belief,
mirroring the monotonic pull toward the ground truth.

The update also has a fixed point at the ground truth. If
`b_s^0 = b_c^0 = b_f^0 = g`, then `b_s^t = g` for all `t`. The property-based
[test_property_coordination_fixed_point.py][tpcfp] samples random `α` and `g`
and confirms the invariant.

[tpdc]: ../../tests/unit/test_property_dialectical_coordination.py
[tpwc]: ../../tests/unit/test_property_weight_convergence.py
[tpcs]: ../../tests/unit/test_property_coordination_stability.py
[tprt]: ../../tests/unit/test_property_ranking_ties.py
[tpcfp]: ../../tests/unit/test_property_coordination_fixed_point.py
[aca]: ../../tests/analysis/agent_coordination_analysis.py
[acm]: ../../tests/analysis/agent_coordination_metrics.json
[tdcp]: ../../tests/analysis/test_dialectical_cycle_property.py

## Agent coordination

[`agent_coordination_analysis.py`][aca] spawns locked processes that increment a
shared counter. The final value matches the expected total, recorded in
[`agent_coordination_metrics.json`][acm], demonstrating proper synchronization.

## Summary

The simulations and property-based tests demonstrate stable ranking under
ties and convergence of coordination updates to fixed points. Stored metrics
support future audits of these behaviors.
