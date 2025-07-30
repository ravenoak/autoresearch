# Search API

This page documents the Search API, which provides search functionality and backends for the Autoresearch system.

## Search Functions

The search module provides functions for searching external sources for information.
`Search.external_lookup` now also performs an embedding-based lookup using the
local storage index so that results from all backends benefit from semantic search.

### Weight Tuning and Optimization

The `tune_weights` utility performs a grid search to find relevance weights that
maximize NDCG on labelled data. `optimize_weights` returns the best weights
together with the achieved score.

::: autoresearch.search.Search.tune_weights
::: autoresearch.search.Search.optimize_weights

::: autoresearch.search.Search.external_lookup

## Search Context

The `SearchContext` class manages search context using a singleton pattern. The
singleton instance can be cleared with `reset_instance()` or temporarily
replaced using `temporary_instance()` when an isolated context is required.

```python
from autoresearch.search import SearchContext

SearchContext.reset_instance()  # ensure a clean state
with SearchContext.temporary_instance() as ctx:
    ctx.add_to_history("example", [])
    # queries inside this block do not affect the global context
```

::: autoresearch.search.SearchContext

## Context-Aware Search

The context-aware search functionality enhances search precision through entity recognition, topic modeling, and search history awareness.

::: autoresearch.config.ContextAwareSearchConfig

## Relevance Ranking

The relevance ranking functionality enhances search results by combining multiple relevance signals.

::: autoresearch.config.SearchConfig





