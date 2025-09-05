# Search Ranking

Autoresearch computes a relevance score for each document using a weighted
combination of multiple signals. The formula is
\(s(d) = w_b b(d) + w_s \frac{m(d) + v(d)}{2} + w_c c(d)\) where:

- \(b(d)\) is the [BM25](bm25.md) keyword score.
- \(m(d)\) is the [semantic similarity](semantic_similarity.md) score.
- \(v(d)\) is the DuckDB vector similarity when available.
- \(c(d)\) is the [domain authority](source_credibility.md) score.

The weights \(w_b\), \(w_s\), and \(w_c\) are non-negative and must sum to
1.0. `semantic_similarity_weight` applies to the average of the embedding and
DuckDB scores.

## Correctness

The final score is a convex combination of component scores, each bounded by
\([0, 1]\). For any document \(d\), the partial derivative with respect to a
component, e.g. \(b(d)\), equals its weight \(w_b \ge 0\). Therefore increasing
any component score strictly increases \(s(d)\). The ordering is thus
monotonic with respect to each signal, and weight normalization preserves the
total order across reruns.

## Complexity

Let \(n\) be the number of documents and \(k\) the number of component scores
available. Computing each score is \(O(k n)\). The final combination is a
linear pass over the scores, giving an overall complexity of \(O(k n)\) per
query.

## References

- R. Baeza-Yates and B. Ribeiro-Neto. *Modern Information Retrieval*.
  https://www.mir2ed.org
- D. Knuth. *The Art of Computer Programming, Volume 3: Sorting and
  Searching*. https://www-cs-faculty.stanford.edu/~knuth/taocp.html

## Simulation

Automated tests confirm search ranking behavior.

- [Spec](../specs/search.md)
- [Tests](../../tests/integration/test_search_ranking_convergence.py)
