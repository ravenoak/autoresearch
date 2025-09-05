# Relevance Ranking

Autoresearch orders search results by a weighted score
\(s(d) = w_b b(d) + w_s m(d) + w_c c(d)\) where
\(b\), \(m\), and \(c\) are BM25, semantic similarity, and source
credibility scores. The non‑negative weights satisfy \(w_b + w_s + w_c = 1\).

## Correctness

### Score bounds

Each component score lies in :math:`[0, 1]` and the weights form a convex
combination. Therefore the final score :math:`s(d)` also lies in
:math:`[0, 1]`.

Sorting by \(s\) is idempotent. Let \(R\) be a list of results and \(T(R)\)
the list sorted by \(s\). Because the scores are fixed, applying \(T\)
again leaves the order unchanged: \(T(T(R)) = T(R)\). Thus repeated ranking
converges in one step to a fixed point.

### Convergence rate

Idempotence implies zero inversions after the first pass. Any initial order
has at most \(n(n-1)/2\) inversions for \(n\) results. After sorting once,
all inversions vanish, giving geometric decay with ratio \(0\).

### Monotonic improvement

Let :math:`R_t` be the ranking after :math:`t` iterations and let
:math:`I(R_t)` count inversions relative to the final order
:math:`R_*`. The sorting operator :math:`T` satisfies
:math:`R_{t+1} = T(R_t)` and guarantees
:math:`I(R_{t+1}) \le I(R_t)` because each pass fixes misplaced pairs.
Since :math:`I(R_1) = 0`, the sequence :math:`I(R_t)` decreases monotonically
to zero. This derivation uses the inversion count formula
:math:`I(R) = |\{(i, j) : i < j, R_i \succ R_j\}|`.

## Complexity

Sorting `n` results by score uses `O(n log n)` time and `O(1)` extra space
when performed in place.

## Simulation

Run `uv run scripts/ranking_convergence.py --items 5` to explore convergence.
[`ranking_convergence.py`](../../scripts/ranking_convergence.py) reports the
iteration when the ordering stabilizes, which is `1` in practice.

Regression tests
[`test_ranking_idempotence.py`](../../tests/unit/test_ranking_idempotence.py)
and
[`test_ranking_convergence.py`](../../tests/unit/test_ranking_convergence.py)
validate idempotence and monotonic improvement.

## References

- R. Baeza-Yates and B. Ribeiro-Neto. *Modern Information Retrieval*.
  https://www.mir2ed.org
- D. Knuth. *The Art of Computer Programming, Volume 3: Sorting and
  Searching*. https://www-cs-faculty.stanford.edu/~knuth/taocp.html
