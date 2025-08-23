# Relevance Ranking

Autoresearch orders search results by a weighted score
\(s(d) = w_b b(d) + w_s m(d) + w_c c(d)\) where
\(b\), \(m\), and \(c\) are BM25, semantic similarity, and source
credibility scores. The non‑negative weights satisfy \(w_b + w_s + w_c = 1\).

## Proof of score bounds

Each component score lies in :math:`[0, 1]` and the weights form a convex
combination. Therefore the final score :math:`s(d)` also lies in
:math:`[0, 1]`.

Sorting by \(s\) is idempotent. Let \(R\) be a list of results and \(T(R)\)
the list sorted by \(s\). Because the scores are fixed, applying \(T\)
again leaves the order unchanged: \(T(T(R)) = T(R)\). Thus repeated ranking
converges in one step to a fixed point.

## Convergence rate

Idempotence implies zero inversions after the first pass. Any initial order
has at most \(n(n-1)/2\) inversions for \(n\) results. After sorting once,
all inversions vanish, giving geometric decay with ratio \(0\).

## Simulation

Run `uv run scripts/ranking_convergence.py --items 5` to verify the
idempotence property empirically. The script reports the iteration when the
ordering stabilizes, which is `1` in practice.

[`ranking_convergence.py`](../../scripts/ranking_convergence.py) contains the
simulation code and prints the final ranking and convergence step.

The regression test
[`test_ranking_idempotence.py`](../../tests/unit/test_ranking_idempotence.py)
confirms that re-ranking a sorted list leaves the order unchanged.

## References

- R. Baeza-Yates and B. Ribeiro-Neto. *Modern Information Retrieval*.
  https://www.mir2ed.org
- D. Knuth. *The Art of Computer Programming, Volume 3: Sorting and
  Searching*. https://www-cs-faculty.stanford.edu/~knuth/taocp.html
