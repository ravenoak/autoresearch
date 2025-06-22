# Search API

This page documents the Search API, which provides search functionality and backends for the Autoresearch system.

## Search Functions

The search module provides functions for searching external sources for information.
`Search.external_lookup` now also performs an embedding-based lookup using the
local storage index so that results from all backends benefit from semantic search.

::: autoresearch.search.Search.external_lookup

## Search Context

The `SearchContext` class manages search context using a singleton pattern.

::: autoresearch.search.SearchContext

## Context-Aware Search

The context-aware search functionality enhances search precision through entity recognition, topic modeling, and search history awareness.

::: autoresearch.config.ContextAwareSearchConfig

## Relevance Ranking

The relevance ranking functionality enhances search results by combining multiple relevance signals.

::: autoresearch.config.SearchConfig





