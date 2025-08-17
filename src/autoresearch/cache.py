"""TinyDB-backed caching utilities for search results.

This module exposes a ``Cache`` class that manages a TinyDB instance and
provides helpers to store and retrieve cached search results. A process-wide
cache instance can be obtained via :func:`get_cache`, while tests or services
can create isolated caches by instantiating :class:`Cache` directly.
"""

from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from tinydb import Query, TinyDB


class Cache:
    """TinyDB-backed cache that can be instantiated per test or service."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = Path(db_path or os.getenv("TINYDB_PATH", "cache.json"))
        self._db_lock = Lock()
        self._db: Optional[TinyDB] = None

    def setup(self, db_path: Optional[str] = None) -> TinyDB:
        """Initialise the TinyDB instance if needed."""
        with self._db_lock:
            if db_path is not None:
                self._db_path = Path(db_path)
            if self._db is None:
                self._db = TinyDB(self._db_path)
            return self._db

    def teardown(self, remove_file: bool = False) -> None:
        """Close the database connection and optionally remove the file."""
        with self._db_lock:
            if self._db is not None:
                self._db.close()
                self._db = None
            if remove_file and self._db_path.exists():
                self._db_path.unlink()

    def get_db(self) -> TinyDB:
        """Return the TinyDB instance, creating it if necessary."""
        return self.setup()

    def cache_results(
        self, query: str, backend: str, results: List[Dict[str, Any]]
    ) -> None:
        """Store search results for a query/backend combination."""
        db = self.get_db()
        db.upsert(
            {"query": query, "backend": backend, "results": results},
            (Query().query == query) & (Query().backend == backend),
        )

    def get_cached_results(
        self, query: str, backend: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached search results if available."""
        db = self.get_db()
        condition = (Query().query == query) & (Query().backend == backend)
        row = db.get(condition)
        if row:
            return list(row.get("results", []))
        return None

    def clear(self) -> None:
        """Clear all cached entries."""
        db = self.get_db()
        if hasattr(db, "drop_tables"):
            db.drop_tables()
        else:
            db.table("_default").truncate()


_global_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Return the process-wide cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = Cache()
    return _global_cache


def setup(db_path: Optional[str] = None) -> TinyDB:
    """Initialise the global cache instance."""
    return get_cache().setup(db_path)


def teardown(remove_file: bool = False) -> None:
    """Tear down the global cache instance."""
    get_cache().teardown(remove_file)


def get_db() -> TinyDB:
    """Return the global TinyDB instance."""
    return get_cache().get_db()


def cache_results(query: str, backend: str, results: List[Dict[str, Any]]) -> None:
    """Store search results for a specific query and backend combination."""
    get_cache().cache_results(query, backend, results)


def get_cached_results(query: str, backend: str) -> Optional[List[Dict[str, Any]]]:
    """Retrieve cached search results for a specific query and backend."""
    return get_cache().get_cached_results(query, backend)


def clear() -> None:
    """Clear all cached entries from the global cache."""
    get_cache().clear()


# Initialise default cache on import
setup()
