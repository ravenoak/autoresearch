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

## Properties

- Increasing any component score strictly increases the final relevance score.
- Adjusting the weights shifts the ranking to emphasize different signals.

## References

- R. Baeza-Yates and B. Ribeiro-Neto. *Modern Information Retrieval*.
  https://www.mir2ed.org
- D. Knuth. *The Art of Computer Programming, Volume 3: Sorting and
  Searching*. https://www-cs-faculty.stanford.edu/~knuth/taocp.html
