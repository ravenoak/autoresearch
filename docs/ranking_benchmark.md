# Ranking Benchmark

Results from `tests/benchmark/test_hybrid_ranking.py` establish baseline
performance for hybrid ranking across search backends.

| Backend | Precision | Recall | Latency (ms) |
|---------|-----------|--------|--------------|
| bm25    | 1.00      | 1.00   | 0.0018       |
| semantic| 0.50      | 1.00   | 0.0019       |
| hybrid  | 0.75      | 1.00   | 0.0023       |

Regression thresholds:

- precision and recall may drop by at most 5 percentage points
- latency may increase by no more than 5%
