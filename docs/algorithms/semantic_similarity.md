# Semantic Similarity Ranking

Autoresearch measures semantic relevance by comparing sentence embeddings with
cosine similarity.

\[
s(D, Q) = \frac{v_q \cdot v_d}{\|v_q\| \|v_d\|}
\]

Scores `s` lie in `[-1, 1]`. They are normalized to `[0, 1]` for ranking:

\[
n(D, Q) = \frac{s(D, Q) + 1}{2}
\]

This scaling allows combination with other non-negative metrics.

## References

- Nils Reimers and Iryna Gurevych. "Sentence-BERT: Sentence Embeddings using
  Siamese BERT-Networks." 2019.
  [https://arxiv.org/abs/1908.10084](https://arxiv.org/abs/1908.10084)

## Simulation

Automated tests confirm semantic similarity behavior.

- [Spec](../specs/search.md)
- [Integration test](../../tests/integration/test_relevance_ranking_integration.py)
- [Unit test](../../tests/unit/test_relevance_ranking.py::test_calculate_semantic_similarity)

The dedicated regression now runs without an `xfail` guard, and the
[SPEC coverage ledger](../../SPEC_COVERAGE.md) links the production scorer
to this unit test.
