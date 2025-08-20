# Algorithm Validation

This document summarizes evaluations of ranking and token budgeting
heuristics.

## Scoring heuristics

Running `uv run scripts/simulate_scoring.py --query "python"` on the
sample dataset produced a ranking consistent with the formula in
[source_credibility.md](source_credibility.md).

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
