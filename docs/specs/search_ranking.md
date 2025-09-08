# Search Ranking

## Overview

The ranking pipeline orders results by combining relevance and recency
scores. BM25 and semantic similarity are merged via a weighted sum that is
applied uniformly across search backends.

## Algorithms

- Weight cosine similarity and metadata freshness.
- Normalize scores before applying a deterministic sort.

## Invariants

- Scores stay within the 0 to 1 range after normalization.
- Equal inputs yield the same ranked order.

## Proof Sketch

Normalization preserves order within each scoring component, and the final sort
is stable, proving deterministic rankings for equal scores.

## Simulation Expectations

- Compare ranking outputs for varied relevance and recency balances.
- Stress test with duplicate items to confirm stability.
- Benchmark precision, recall, and latency across backends with shared
  datasets. Results appear in [docs/ranking_benchmark.md][d1], and
  regression thresholds flag precision or recall drops over five
  percentage points or latency increases above five percent.

## Traceability

- Code: [src/autoresearch/search/ranking_convergence.py][m1]
- Tests:
  - [tests/behavior/features/search_cli.feature][t1]
  - [tests/behavior/features/hybrid_search.feature][t2]
  - [tests/benchmark/test_hybrid_ranking.py][t3]
  - [docs/ranking_benchmark.md][d1]

[m1]: ../../src/autoresearch/search/ranking_convergence.py
[t1]: ../../tests/behavior/features/search_cli.feature
[t2]: ../../tests/behavior/features/hybrid_search.feature
[t3]: ../../tests/benchmark/test_hybrid_ranking.py
[d1]: ../ranking_benchmark.md
