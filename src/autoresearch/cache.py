"""TinyDB-backed caching utilities for search results.

This module previously exposed a set of module-level functions operating on a
global TinyDB instance. To better support test isolation and service
composition, the cache is now provided as the :class:`SearchCache` class which
can be instantiated as needed. A shared instance is still provided for
backwards compatibility, and thin wrapper functions mirror the original API.
"""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from tinydb import TinyDB, Query


_db_path: Path = Path(os.getenv("TINYDB_PATH", "cache.json"))


class SearchCache:
    """TinyDB-backed cache that can be instantiated per test or service."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_lock = Lock()
        self._db: Optional[TinyDB] = None
        self._db_path = Path(db_path) if db_path is not None else _db_path
        # Eagerly initialise so the file exists for tests
        self.setup()

    def setup(self, db_path: Optional[str] = None) -> TinyDB:
        """Initialise the TinyDB instance if needed."""
        with self._db_lock:
            path = Path(db_path) if db_path is not None else self._db_path
            if self._db is None or path != self._db_path:
                self._db_path = path
                self._db = TinyDB(self._db_path)
            return self._db

    def teardown(self, remove_file: bool = False) -> None:
        """Close the database connection and optionally remove the cache file."""
        with self._db_lock:
            if self._db is not None:
                self._db.close()
                self._db = None
            if remove_file and self._db_path.exists():
                self._db_path.unlink()

    def get_db(self) -> TinyDB:
        """Return the underlying TinyDB instance, initialising if necessary."""
        return self.setup()

    def cache_results(
        self, query: str, backend: str, results: List[Dict[str, Any]]
    ) -> None:
        """Store search results for a specific query/backend combination."""
        db = self.get_db()
        db.upsert(
            {
                "query": query,
                "backend": backend,
                "results": deepcopy(results),
            },
            (Query().query == query) & (Query().backend == backend),
        )

    def get_cached_results(
        self, query: str, backend: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached search results for a query/backend pair."""
        db = self.get_db()
        condition = (Query().query == query) & (Query().backend == backend)
        row = db.get(condition)
        if row:
            return deepcopy(row.get("results", []))
        return None

    def clear(self) -> None:
        """Remove all cached entries."""
        db = self.get_db()
        if hasattr(db, "drop_tables"):
            db.drop_tables()
        else:  # pragma: no cover - tinydb < 4
            db.table("_default").truncate()


_shared_cache = SearchCache()


def get_cache() -> SearchCache:
    """Return the module's shared :class:`SearchCache` instance."""
    return _shared_cache


# ---------------------------------------------------------------------------
# Backwards compatible functional API


def setup(db_path: Optional[str] = None) -> TinyDB:  # pragma: no cover - legacy
    return get_cache().setup(db_path)


def teardown(remove_file: bool = False) -> None:  # pragma: no cover - legacy
    get_cache().teardown(remove_file)


def get_db() -> TinyDB:  # pragma: no cover - legacy
    return get_cache().get_db()


def cache_results(query: str, backend: str, results: List[Dict[str, Any]]) -> None:
    get_cache().cache_results(query, backend, results)


def get_cached_results(query: str, backend: str) -> Optional[List[Dict[str, Any]]]:
    return get_cache().get_cached_results(query, backend)


def clear() -> None:
    get_cache().clear()


__all__ = [
    "SearchCache",
    "get_cache",
    "setup",
    "teardown",
    "get_db",
    "cache_results",
    "get_cached_results",
    "clear",
]
