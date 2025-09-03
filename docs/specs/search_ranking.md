# Search Ranking

## Overview

The ranking pipeline orders results by combining relevance and recency scores.

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

## Traceability

- [src/autoresearch/search/ranking_convergence.py][m1]
- [tests/behavior/features/search_cli.feature][t1]
- [tests/behavior/features/hybrid_search.feature][t2]

[m1]: ../../src/autoresearch/search/ranking_convergence.py
[t1]: ../../tests/behavior/features/search_cli.feature
[t2]: ../../tests/behavior/features/hybrid_search.feature
