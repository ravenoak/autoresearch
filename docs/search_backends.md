# Configuring Search Backends

Autoresearch can combine results from multiple search backends. By default the
system merges all responses and ranks them together using a hybrid algorithm
that mixes BM25 keyword scores, semantic similarity and source credibility.

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
ranking across all backends. Semantic and DuckDB vector similarities are
normalized before averaging so hybrid and semantic results share a common
scale. If the vector store yields no matches the semantic scores are used
directly to avoid downscaling.

Weights are configured as follows and must sum to `1.0`:

```toml
[search]
semantic_similarity_weight = 0.6
bm25_weight = 0.3
source_credibility_weight = 0.1
```

The ranking formula normalizes each component to the `0`–`1` range and
then applies a weighted sum:

```
score = bm25_norm * bm25_weight
        + semantic_norm * semantic_similarity_weight
        + credibility_norm * source_credibility_weight
```

The combined scores are normalized again before sorting so the highest
ranked item always receives `1.0`.

Use `scripts/optimize_search_weights.py` with a labelled evaluation dataset to
automatically discover good values. The script runs a grid search and updates
the configuration file with the best-performing weights.

## Hot reload

Changes to the `[search]` section are applied at runtime. The configuration
watcher updates active search backends and weights without restarting
services.

## Cache determinism

Search caching relies on a composite key that combines the backend name, the
normalized query text, and the embedding-related switches (hybrid queries,
semantic similarity, and the configured embedding backends). This contract
avoids stale hits when embedding options change during a session.

When every configured backend fails, the fallback backend publishes
deterministic placeholder results under the `__fallback__` namespace. The
placeholder URLs encode the query and rank so repeated failures remain
reproducible and visible in cache diagnostics.

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

## Knowledge graph conditioning

Context-aware search can enrich the planner and gate policy with knowledge graph
signals. Configure these options in the `[search.context_aware]` section:

```toml
[search.context_aware]
graph_signal_weight = 0.2
planner_graph_conditioning = true
graph_pipeline_enabled = true
graph_contradiction_weight = 0.3
```

- `graph_signal_weight` scales supportive similarity signals derived from the
  knowledge graph.
- `planner_graph_conditioning` injects contradictions, neighbour snippets, and
  provenance sources into planner prompts when enabled.
- `graph_pipeline_enabled` toggles the session GraphRAG ingest loop. When the
  pipeline is active, `OrchestrationMetrics` exports `graph_ingestion`
  counters with entity, relation, contradiction, neighbour, and latency
  aggregates.
- `graph_contradiction_weight` tunes how strongly contradictions influence the
  gate policy and the exported weighted scores.

Gate policy thresholds live at the top level of the configuration:

```toml
gate_graph_contradiction_threshold = 0.25
gate_graph_similarity_threshold = 0.0
```

Tuning these values lets you balance how strongly graph contradictions or sparse
similarity encourage a multi-agent debate.
