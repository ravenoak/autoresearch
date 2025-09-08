# Configuring Search Backends

Autoresearch can combine results from multiple search backends. By default the
system merges all responses and ranks them together using a hybrid algorithm
that mixes [BM25 keyword scores](algorithms/bm25.md),
[semantic similarity](algorithms/semantic_similarity.md) and
[source credibility](algorithms/source_credibility.md).

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
automatically discover good values. The script runs a grid search and updates
the configuration file with the best-performing weights.

## Hot reload

Changes to the `[search]` section are applied at runtime. The configuration
watcher updates active search backends and weights without restarting
services.

## Benchmarking

To guard against regressions, run `uv run pytest`
`tests/benchmark/test_hybrid_ranking.py` with the shared dataset in
`tests/data/backend_benchmark.csv`. Example results and thresholds live in
[ranking_benchmark.md](ranking_benchmark.md). The test stores baseline
metrics in `tests/data/backend_metrics.json` and fails if precision, recall
or latency regress by more than 5\%.

### Benchmark results

On 2025-09-07, running
`uv run --extra test pytest tests/benchmark/test_hybrid_ranking.py -m slow`
produced:

| Backend | Precision | Recall | Mean latency (µs) |
|---------|-----------|--------|-------------------|
| bm25    | 1.00      | 1.00   | 1.93              |
| semantic| 0.50      | 1.00   | 1.99              |
| hybrid  | 0.75      | 1.00   | 2.20              |
