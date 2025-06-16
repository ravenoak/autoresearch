# Search API

This page documents the Search API, which provides search functionality and backends for the Autoresearch system.

## Search Functions

The search module provides functions for searching external sources for information.

::: autoresearch.search.external_lookup
::: autoresearch.search.search

## Search Context

The `SearchContext` class manages search context using a singleton pattern.

::: autoresearch.search.SearchContext

## Context-Aware Search

The context-aware search functionality enhances search precision through entity recognition, topic modeling, and search history awareness.

::: autoresearch.search.ContextAwareSearchConfig

## Relevance Ranking

The relevance ranking functionality enhances search results by combining multiple relevance signals.

::: autoresearch.search.SearchConfig

## Search Backends

### Serper Backend

The `SerperBackend` class provides integration with the Serper.dev search API.

::: autoresearch.search.SerperBackend

### Brave Backend

The `BraveBackend` class provides integration with the Brave Search API.

::: autoresearch.search.BraveBackend

### Local Backend

The `LocalBackend` class provides search functionality for local documents.

::: autoresearch.search.LocalBackend