# Search Ranking

## Overview

The ranking pipeline orders results by combining relevance and recency
scores. BM25 and semantic similarity are merged via a weighted sum that is
applied uniformly across search backends.

## Algorithms

- Weight cosine similarity and metadata freshness.
- Normalize scores with min–max scaling before applying a deterministic sort.
- When hierarchical traversal is active, multiply the normalized blend by the
  path relevance score ``r_p``. The runtime computes ``r_p`` from the latent
  edge estimates and an exponential moving average with decay ``\beta``.
- Clamp ``r_p`` to ``[0.4, 1.4]`` so extreme path swings do not swamp BM25 or
  semantic evidence. The clamp thresholds surface through telemetry as
  ``path_relevance_min`` and ``path_relevance_max`` knobs.

## Example

Consider two documents with raw scores:

```
bm25 = [3, 1]
semantic = [0.8, 0.2]
credibility = [0.9, 0.5]
```

Min–max normalization maps each component to `1` and `0`. Applying weights of
`0.5`, `0.3`, and `0.2` produces combined scores of `1.0` and `0.0`. A final
normalization step keeps the results within the `0` to `1` range.

## Invariants

- Scores stay within the 0 to 1 range after normalization.
- Equal inputs yield the same ranked order.
- If ``hierarchy_quality`` drops below ``0.62`` or the telemetry feed for
  ``momentum_drift`` exceeds ``0.18`` for three successive slates, ``r_p``
  resets to ``1.0`` and the system falls back to the baseline hybrid weighting.
- Path relevance composition preserves monotonicity with respect to BM25 and
  semantic scores because ``r_p`` remains positive and clamps avoid sign flips.

## Proof Sketch

Normalization maps all component scores to the unit interval while maintaining
their relative ordering. The weighted sum is therefore bounded by `0` and `1`,
and the subsequent stable sort ensures that ties preserve input order. Thus,
equal inputs deterministically produce the same ranking.

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
