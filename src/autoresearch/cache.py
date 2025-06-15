"""TinyDB-backed caching utilities for search results.

This module provides a simple caching system for search results using TinyDB,
a lightweight document-oriented database. It allows storing and retrieving
search results for specific query and backend combinations, which can significantly
improve performance by avoiding redundant searches for previously seen queries.

The cache is automatically initialized on module import with a default path,
which can be overridden using the TINYDB_PATH environment variable or by
explicitly calling the setup function with a custom path.

The module uses a global TinyDB instance with thread-safety ensured through
a lock mechanism, making it safe to use in multi-threaded environments.

Typical usage:
    ```python
    from autoresearch import cache

    # Store search results
    cache.cache_results("my query", "google", [{"title": "Result 1", "url": "..."}])

    # Retrieve cached results
    results = cache.get_cached_results("my query", "google")

    # Clear the cache
    cache.clear()

    # Close the database when done
    cache.teardown()
    ```
"""

from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from tinydb import TinyDB, Query

_db_lock = Lock()
_db: Optional[TinyDB] = None
_db_path = Path(os.getenv("TINYDB_PATH", "cache.json"))


def setup(db_path: Optional[str] = None) -> TinyDB:
    """Initialize the TinyDB instance if needed.

    This function initializes the global TinyDB instance used for caching.
    If the instance already exists, it returns the existing instance.
    If a custom database path is provided, it updates the path before
    initializing the database.

    The function is thread-safe, using a lock to prevent race conditions
    when multiple threads attempt to initialize the database simultaneously.

    Args:
        db_path (Optional[str], optional): Custom path for the TinyDB database file.
            If None, uses the current path (default from environment or previous setup).
            Defaults to None.

    Returns:
        TinyDB: The initialized TinyDB instance.
    """
    global _db, _db_path
    with _db_lock:
        if db_path is not None:
            _db_path = Path(db_path)
        if _db is None:
            _db = TinyDB(_db_path)
        return _db


def teardown(remove_file: bool = False) -> None:
    """Close the database connection and optionally remove the cache file.

    This function properly closes the TinyDB connection and optionally
    removes the database file from disk. It's important to call this
    function when the cache is no longer needed to ensure proper resource
    cleanup.

    The function is thread-safe, using a lock to prevent race conditions
    when multiple threads attempt to close the database simultaneously.

    Args:
        remove_file (bool, optional): If True, the database file will be
            deleted from disk after closing the connection. Defaults to False.

    Returns:
        None
    """
    global _db
    with _db_lock:
        if _db is not None:
            _db.close()
            _db = None
        if remove_file and _db_path.exists():
            _db_path.unlink()


def get_db() -> TinyDB:
    """Get the global TinyDB instance, initializing it if necessary.

    This function is a convenience wrapper around the setup() function
    that ensures the database is initialized before returning it.
    It's the recommended way to access the database instance throughout
    the application.

    Returns:
        TinyDB: The initialized TinyDB instance.

    Example:
        ```python
        from autoresearch.cache import get_db

        db = get_db()
        results = db.search(Query().query == "my query")
        ```
    """
    return setup()


def cache_results(
    query: str, backend: str, results: List[Dict[str, Any]]
) -> None:
    """Store search results for a specific query and backend combination.

    This function caches the search results for a given query and backend
    combination. If results for this combination already exist in the cache,
    they will be updated with the new results (upsert operation).

    Caching results can significantly improve performance for repeated queries
    by avoiding redundant searches to external services or databases.

    Args:
        query (str): The search query string.
        backend (str): The name of the search backend (e.g., "google", "bing").
        results (List[Dict[str, Any]]): The search results to cache, as a list
            of dictionaries. Each dictionary should represent a single search result
            with any structure appropriate for the backend.

    Returns:
        None

    Example:
        ```python
        results = [
            {"title": "Result 1", "url": "https://example.com/1"},
            {"title": "Result 2", "url": "https://example.com/2"}
        ]
        cache_results("climate change", "google", results)
        ```
    """
    db = get_db()
    db.upsert(
        {"query": query, "backend": backend, "results": results},
        (Query().query == query) & (Query().backend == backend),
    )


def get_cached_results(
    query: str, backend: str
) -> Optional[List[Dict[str, Any]]]:
    """Retrieve cached search results for a specific query and backend combination.

    This function attempts to retrieve previously cached search results for the
    given query and backend combination. If no results are found in the cache,
    it returns None, indicating that a new search should be performed.

    Args:
        query (str): The search query string.
        backend (str): The name of the search backend (e.g., "google", "bing").

    Returns:
        Optional[List[Dict[str, Any]]]: A list of search result dictionaries if
            found in the cache, or None if no cached results exist for the
            specified query and backend combination.

    Example:
        ```python
        # Check if we have cached results before performing a new search
        cached_results = get_cached_results("climate change", "google")
        if cached_results:
            # Use cached results
            process_results(cached_results)
        else:
            # Perform new search
            new_results = perform_search("climate change", "google")
            cache_results("climate change", "google", new_results)
            process_results(new_results)
        ```
    """
    db = get_db()
    condition = (Query().query == query) & (Query().backend == backend)
    row = db.get(condition)
    if row:
        return list(row.get("results", []))
    return None


def clear() -> None:
    """Clear all cached entries from the database.

    This function removes all cached search results from the database,
    effectively resetting the cache to an empty state. The database file
    itself is not deleted, only its contents are cleared.

    This can be useful in several scenarios:
    - When testing to ensure a clean state
    - When the cache has grown too large
    - When you want to force fresh searches for all queries
    - When the search backend has been updated and old results may be stale

    Returns:
        None

    Example:
        ```python
        from autoresearch.cache import clear

        # Clear all cached search results
        clear()
        ```
    """
    db = get_db()
    db.truncate()


# Initialise default cache on import
setup()
