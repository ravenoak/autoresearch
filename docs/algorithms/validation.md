# Algorithm Validation

This document summarizes evaluations of ranking and token budgeting
heuristics.

## Scoring heuristics

Running `uv run scripts/simulate_scoring.py --query "python"` on the
sample dataset produced a ranking consistent with the formula in
[source_credibility.md](source_credibility.md).

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

## Coordination policies

[tests/analysis/dialectical_cycle_analysis.py]
(../../tests/analysis/dialectical_cycle_analysis.py) runs 100 trials of the
dialectical update with noise `0.1` and stores the final mean and deviation
in
[dialectical_metrics.json](../../tests/analysis/dialectical_metrics.json).
The results match the convergence bound in
[dialectical_coordination.md](dialectical_coordination.md). A property-based
test, [test_property_dialectical_coordination.py][tpdc], validates
convergence to the ground truth in the noiseless case.

[tpdc]: ../../tests/unit/test_property_dialectical_coordination.py
