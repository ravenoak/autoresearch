# Ranking Benchmark

Results from `tests/benchmark/test_hybrid_ranking.py` establish baseline
performance for hybrid ranking across search backends. The hybrid algorithm uses
weights of 0.4 for BM25, 0.5 for semantic similarity, and 0.1 for source
credibility.

| Backend | Precision | Recall | Latency (ms) |
|---------|-----------|--------|--------------|
| bm25    | 1.00      | 1.00   | 0.0026       |
| semantic| 0.50      | 1.00   | 0.0027       |
| hybrid  | 0.75      | 1.00   | 0.0031       |

Regression thresholds:

- precision and recall may drop by at most 5 percentage points
- latency may increase by no more than 5%
