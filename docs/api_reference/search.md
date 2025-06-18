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

### Local File Backend

The `LocalFileBackend` class indexes documents from local directories. Configure the backend in `[search.local_file]` with a `path` to the root directory and a list of allowed `file_types`.

Results contain a text `snippet` and the absolute `path` to the file.

Caching avoids reprocessing unchanged files by storing a modification timestamp in the index. Only new or updated files are re-indexed on subsequent runs.

::: autoresearch.search.LocalFileBackend

### Git Backend

The `GitBackend` class searches a local Git repository. Configure it in `[search.local_git]` with `repo_path`, `branches`, and `history_depth` to limit indexing depth.

Each indexed entry stores the file `path`, commit `hash`, and a brief `snippet`. Incremental indexing keeps the database synced with the repository without reprocessing unchanged commits.

::: autoresearch.search.GitBackend
