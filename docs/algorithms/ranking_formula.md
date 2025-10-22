# Ranking Formula

Autoresearch ranks documents by the convex combination
\(s(d) = w_b b(d) + w_s m(d) + w_c c(d)\) where
\(b\), \(m\), and \(c\) denote the BM25, semantic similarity, and source
credibility scores. The non negative weights satisfy \(w_b + w_s + w_c = 1\).

Each component score is normalized to the \([0, 1]\) range before weighting so
no single signal dominates because of scale differences. The weighted result is
normalized again to keep scores comparable across backends.

## Latent score estimation

Hierarchical traversal observes slate-level path scores \(s_{i, v}\) for slate
\(i\) and vertex \(v\). The latent formulation calibrates these observations to
global structure by minimizing the squared error between measured scores and a
shared linear model with per-slate offsets. Let \(a\) be a global scale,
\(b_i\) the bias for slate \(i\), and \(\hat{s}_v\) the latent canonical score
assigned to vertex \(v\). The estimator solves

\[
\min_{a,\,\{b_i\},\,\{\hat{s}_v\}} \sum_{i, v}\Bigl(s_{i, v} -
\bigl(a\,\hat{s}_v + b_i\bigr)\Bigr)^2.
\]

This least-squares program jointly recovers the global calibration factor, the
slate-specific offsets, and the latent vertex scores that are later consumed by
the traversal logic.

## Exponential moving-average path relevance

Path relevance combines the calibrated latent scores along a traversal with an
exponential moving average (EMA) that damps volatility while keeping recent
signals responsive. For path score \(r_t\) at iteration \(t\) and instantaneous
score \(s_t\), the recurrence is

\[
r_t = \alpha s_t + (1 - \alpha) r_{t-1},
\]

with smoothing parameter \(\alpha = 0.5\) by default. The EMA seeds with the
current \(\hat{s}_v\) of the entry vertex so calibrated scores immediately
inform the path multiplier. The aggregated value is clamped to ``[0.4, 1.4]`` to
preserve stability before forwarding to the hybrid ranker.

## Proof of convex bounds

Each component score lies in :math:`[0, 1]`. Because the weights sum to one,
the final score is a convex combination and also resides in :math:`[0, 1]`.
Increasing any component score strictly increases the final relevance score.
This property ensures consistent ranking across repeated evaluations.

## Proof sketch from information retrieval theory

The probability ranking principle (PRP) states that ordering documents by
their probability of relevance yields optimal retrieval. BM25, semantic
similarity, and source credibility each approximate this probability from
distinct evidence sources. Their non-negative weights form a convex mixture, so
the combined score preserves the ordering mandated by the PRP and remains a
consistent relevance estimator.

## Proof sketch for latent calibration

The least-squares calibration yields bounded mean-squared error because the
objective is strongly convex in \(a\), \(\{b_i\}\), and \(\{\hat{s}_v\}\) when
the design matrix has full rank, providing a closed-form solution with
well-characterized residuals. The resulting \(\hat{s}_v\) remain within a
bounded affine transformation of the observed \(s_{i, v}\), and the EMA keeps
path scores in a compact interval. LATTICE ablations report that removing
either the path smoothing or the calibration layer degrades normalized
discounted cumulative gain (nDCG), establishing that the combined procedure
controls error while sustaining ranking quality.

## Simulation across datasets

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
