# Ranking Formula

Autoresearch ranks documents by the convex combination
\(s(d) = w_b b(d) + w_s m(d) + w_c c(d)\) where
\(b\), \(m\), and \(c\) denote the BM25, semantic similarity, and source
credibility scores. The non negative weights satisfy \(w_b + w_s + w_c = 1\).

## Correctness

Each component score lies in :math:`[0, 1]`. Because the weights sum to one,
the final score is a convex combination and also resides in :math:`[0, 1]`.
Increasing any component score strictly increases the final relevance score,
ensuring consistent ordering across evaluations. The probability ranking
principle states that ordering documents by their relevance probability yields
optimal retrieval. BM25, semantic similarity, and source credibility each
approximate this probability from distinct evidence sources. Their non-negative
weights form a convex mixture, preserving the ordering mandated by the
principle and maintaining a coherent relevance estimate.

## Complexity

Let \(n\) be the number of documents and \(k = 3\) the component scores. Given
precomputed scores, combining them is a single pass over the documents for
\(O(k n)\) time and \(O(1)\) additional space per document.

## Simulation

Synthetic datasets with differing noise levels confirm that noisier data
reduces ranking quality. The chart below plots the normalized discounted
cumulative gain (NDCG) for datasets with noise parameters `0.0` and `0.3`.

![NDCG by dataset noise](../images/ranking_dataset_ndcg.svg)

## References

- R. Baeza-Yates and B. Ribeiro-Neto. *Modern Information Retrieval*.
  https://www.mir2ed.org
- D. Knuth. *The Art of Computer Programming, Volume 3: Sorting and
  Searching*. https://www-cs-faculty.stanford.edu/~knuth/taocp.html
- S. E. Robertson. "The Probability Ranking Principle in IR." *Journal of
  Documentation*, 1977. https://doi.org/10.1108/eb026648
