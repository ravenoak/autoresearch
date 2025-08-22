# Weight Tuning

Combining BM25, semantic similarity, and source credibility uses a
convex weight vector \(w = [w_s, w_b, w_c]\). The final score for
one document is
\(s_i = w_s s_i^{sem} + w_b s_i^{bm25} + w_c s_i^{cred}\).
We seek weights that maximize ranking quality. With a mean squared error
loss \(L = \sum_i (y_i - s_i)^2\), the gradient for each weight is
\(\partial L/\partial w_j = -2 \sum_i (y_i - s_i) f_{ij}\), where
\(f_{ij}\) is feature \(j\) for document \(i\). Repeated updates

\(w_{t+1} = \text{normalize}(w_t - \eta \nabla L)\)

converge for small \(\eta\) because \(L\) is convex in \(w\).
[`weight_tuning_convergence.py`](../../scripts/weight_tuning_convergence.py)
demonstrates convergence and robustness: several random initializations yield
similar final weights and losses.

Solving the normal equations of the unconstrained problem
\(\min_w \|F w - y\|_2^2\) gives
\(w^* = (F^T F)^{-1} F^T y\). Projecting \(w^*\) onto the simplex
enforces non-negative weights summing to one and matches the normalized
gradient update above.

`[evaluate_ranking.py](../../scripts/evaluate_ranking.py)` assesses weight
quality on labelled data. Running
`uv run scripts/evaluate_ranking.py examples/search_evaluation.csv`
reports `Precision@1: 0.00  Recall@1: 0.00`, motivating careful tuning.

Assumptions
- Features are normalized to the \([0, 1]\) range.
- Weights remain on the simplex and non-negative.

Alternatives
- Pairwise learning-to-rank methods such as RankNet [1].
- Bayesian optimization for direct NDCG maximization [2].

Conclusions
- Simple gradient descent reaches stable weights with low variance across
  seeds, supporting reproducible search ranking.

## References
1. C. Burges et al. "Learning to Rank with Gradient Descent."
   https://doi.org/10.1145/1102351.1102363
2. M. Zitouni. "Optimizing NDCG Measures using Gradient Descent."
   https://arxiv.org/abs/2003.06491
