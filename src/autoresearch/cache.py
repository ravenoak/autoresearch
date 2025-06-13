"""TinyDB-backed caching utilities."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from tinydb import TinyDB, Query  # type: ignore

_db_lock = Lock()
_db: Optional[TinyDB] = None
_db_path = Path(os.getenv("TINYDB_PATH", "cache.json"))


def setup(db_path: Optional[str] = None) -> TinyDB:
    """Initialise the TinyDB instance if needed."""
    global _db, _db_path
    with _db_lock:
        if db_path is not None:
            _db_path = Path(db_path)
        if _db is None:
            _db = TinyDB(_db_path)
        return _db


def teardown(remove_file: bool = False) -> None:
    """Close the DB and optionally remove the file."""
    global _db
    with _db_lock:
        if _db is not None:
            _db.close()
            _db = None
        if remove_file and _db_path.exists():
            _db_path.unlink()


def get_db() -> TinyDB:
    """Return the TinyDB instance."""
    return setup()


def cache_results(
    query: str, backend: str, results: List[Dict[str, Any]]
) -> None:
    """Store search results for a query/backend combination."""
    db = get_db()
    db.upsert(
        {"query": query, "backend": backend, "results": results},
        (Query().query == query) & (Query().backend == backend),
    )


def get_cached_results(
    query: str, backend: str
) -> Optional[List[Dict[str, Any]]]:
    """Retrieve cached results for a query/backend if present."""
    db = get_db()
    condition = (Query().query == query) & (Query().backend == backend)
    row = db.get(condition)
    if row:
        return list(row.get("results", []))
    return None


def clear() -> None:
    """Clear all cached entries."""
    db = get_db()
    db.truncate()


# Initialise default cache on import
setup()
