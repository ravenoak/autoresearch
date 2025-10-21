# Ranking Formula

Autoresearch ranks documents by the convex combination
\(s(d) = w_b b(d) + w_s m(d) + w_c c(d)\) where
\(b\), \(m\), and \(c\) denote the BM25, semantic similarity, and source
credibility scores. The non negative weights satisfy \(w_b + w_s + w_c = 1\).

Each component score is normalized to the \([0, 1]\) range before weighting so
no single signal dominates because of scale differences. The weighted result is
normalized again to keep scores comparable across backends.

## Latent score estimation

Hierarchical traversal introduces latent edge scores \(\theta_{ij}\) that
capture how a parent node \(i\) routes toward child \(j\). Observed traversal
clicks or acceptance events provide counts \(n_{ij}\) with successes
\(k_{ij}\). The runtime estimates \(\theta_{ij}\) with a constrained maximum
likelihood objective:

\[
\hat{\theta}_{ij} = \arg\max_{\theta \ge 0,\ \sum_j \theta_{ij} = 1} \sum_j
\Bigl[k_{ij} \log \theta_{ij} + (n_{ij} - k_{ij}) \log (1 - \theta_{ij})\Bigr]
\]

The projection step enforces the simplex constraint and maintains non-negative
branch priors. Telemetry exposes the ``latent_score_prior`` pseudo-counts so
operators can tune the smoothing term applied before optimization.

## Exponential moving-average path relevance

Path relevance combines the latent edge estimates along a traversal with an
exponential moving average (EMA) to temper volatility. For a path score
\(r_t\) at iteration \(t\) and instantaneous score \(s_t\):

\[
r_t = (1 - \beta) s_t + \beta r_{t-1}
\]

where \(\beta \in [0, 1)\) arrives from telemetry as ``momentum_beta``. The
EMA resets to \(1.0\) when hierarchy diagnostics signal low quality. The path
multiplier forwarded to the hybrid ranker is \(r_t\) clamped to
``[0.4, 1.4]``; the clamp endpoints remain configurable via
``path_relevance_min`` and ``path_relevance_max``.

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

The constrained maximum-likelihood estimator minimizes the empirical negative
log-likelihood, which upper bounds mean squared error when the gradients are
Lipschitz. The LATTICE calibration report shows that projecting onto the
probability simplex after each update yields MSE within \(\epsilon\) of the
oracle estimate under misspecification noise. Because the EMA multiplier keeps
\(r_t\) within bounded variation and clamp thresholds prevent divergence, the
composed score preserves the LATTICE guarantee: expected calibration error and
MSE remain within the documented tolerances when ``hierarchy_quality`` stays
above ``0.62`` and ``momentum_drift`` below ``0.18``. These thresholds must be
surfaced as telemetry parameters for operational overrides.

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
