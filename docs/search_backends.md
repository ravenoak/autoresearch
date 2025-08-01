# Configuring Search Backends

Autoresearch can combine results from multiple search backends. By default the
system merges all responses and ranks them together using a hybrid algorithm
that mixes BM25 keyword scores, semantic similarity of embeddings and the
credibility of each source.

Enable or disable backends in the `[search]` section of `autoresearch.toml`:

```toml
[search]
backends = ["serper", "local_file", "local_git"]
embedding_backends = ["duckdb"]
hybrid_query = true
```

When `hybrid_query` is `true` every query is converted to a vector embedding in
addition to regular keyword lookup. Scores from BM25, semantic similarity and
source credibility are combined according to their weights to produce a unified
ranking across all backends.

Weights are configured as follows and must sum to `1.0`:

```toml
[search]
semantic_similarity_weight = 0.6
bm25_weight = 0.3
source_credibility_weight = 0.1
```

Use `scripts/optimize_search_weights.py` with a labelled evaluation dataset to
automatically discover good values. The script runs a grid search and updates the
configuration file with the best-performing weights.
