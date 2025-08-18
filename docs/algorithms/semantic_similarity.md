# Semantic Similarity Ranking

Autoresearch measures semantic relevance by comparing sentence embeddings.

\[score(D, Q) = \frac{v_q \cdot v_d}{\|v_q\| \|v_d\|}\]

The cosine similarity between the query vector `v_q` and a document vector `v_d`
produces scores in the `[-1, 1]` range. No additional normalization is applied.

## References

- Nils Reimers and Iryna Gurevych. "Sentence-BERT: Sentence Embeddings using
  Siamese BERT-Networks." 2019. [https://arxiv.org/abs/1908.10084](https://arxiv.org/abs/1908.10084)
