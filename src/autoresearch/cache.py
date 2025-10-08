"""TinyDB-backed caching utilities for search results.

This module previously exposed a set of module-level functions operating on a
global TinyDB instance. To better support test isolation and service
composition, the cache is now provided as the :class:`SearchCache` class which
can be instantiated as needed. A shared instance is still provided for
backwards compatibility, and thin wrapper functions mirror the original API.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass
from hashlib import blake2b
from pathlib import Path
from threading import Lock
from typing import Any, cast
import re

from tinydb import TinyDB, Query


_db_path: Path = Path(os.getenv("TINYDB_PATH", "cache.json"))


_WHITESPACE_PATTERN = re.compile(r"\s+")


class SearchCache:
    """TinyDB-backed cache that can be instantiated per test or service."""

    def __init__(self, db_path: str | None = None, *, namespace: str | None = None) -> None:
        self._db_lock = Lock()
        self._db: TinyDB | None = None
        self._namespace = namespace or "__default__"
        # Use a per-instance ephemeral path under pytest to avoid cross-test leakage
        if db_path is None and os.environ.get("PYTEST_CURRENT_TEST"):
            from pathlib import Path as _P
            tmpdir = _P(".pytest_cache")
            tmpdir.mkdir(exist_ok=True)
            self._db_path = tmpdir / f"tinydb_{os.getpid()}_{id(self)}.json"
        else:
            self._db_path = Path(db_path) if db_path is not None else _db_path
        # Eagerly initialise so the file exists for tests
        self.setup()

    def setup(self, db_path: str | None = None) -> TinyDB:
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

    def _resolve_namespace(self, namespace: str | None) -> str:
        return namespace or self._namespace

    def cache_results(
        self,
        query: str,
        backend: str,
        results: list[dict[str, Any]],
        *,
        namespace: str | None = None,
    ) -> None:
        """Store search results for a specific query/backend combination."""
        db = self.get_db()
        ns = self._resolve_namespace(namespace)
        db.upsert(
            {
                "namespace": ns,
                "query": query,
                "backend": backend,
                "results": deepcopy(results),
            },
            (Query().namespace == ns)
            & (Query().query == query)
            & (Query().backend == backend),
        )

    def get_cached_results(
        self,
        query: str,
        backend: str,
        *,
        namespace: str | None = None,
    ) -> list[dict[str, Any]] | None:
        """Retrieve cached search results for a query/backend pair."""
        db = self.get_db()
        ns = self._resolve_namespace(namespace)
        condition = (
            (Query().namespace == ns)
            & (Query().query == query)
            & (Query().backend == backend)
        )
        row = cast(dict[str, Any] | None, db.get(condition))
        if row:
            results_raw = cast(list[dict[str, Any]], row.get("results", []))
            return deepcopy(results_raw)
        return None

    def clear(self, namespace: str | None = None) -> None:
        """Remove cached entries, optionally scoped by namespace."""
        db = self.get_db()
        ns = self._resolve_namespace(namespace)
        if namespace is None and ns == self._namespace:
            if hasattr(db, "drop_tables"):
                db.drop_tables()
            else:  # pragma: no cover - tinydb < 4
                db.table("_default").truncate()
            return
        table = db.table("_default")
        table.remove(Query().namespace == ns)

    def namespaced(self, namespace: str | None) -> SearchCache | _SearchCacheView:
        """Return a view of this cache that isolates entries to ``namespace``."""

        if not namespace:
            return self
        return _SearchCacheView(self, namespace)


@dataclass(frozen=True)
class CacheKey:
    """Encapsulate cache key material for legacy and hashed lookups."""

    primary: str
    legacy: str
    aliases: tuple[str, ...] = ()
    fingerprint: str | None = None

    def candidates(self) -> tuple[str, ...]:
        """Return key variants to attempt during cache lookups."""

        seen: list[str] = []
        for candidate in (self.primary, *self.aliases, self.legacy):
            if candidate in seen:
                continue
            seen.append(candidate)
        return tuple(seen)


def hash_cache_dimensions(
    *,
    namespace: str | None,
    canonical_query: str,
    embedding_signature: Sequence[str],
    hybrid_flags: Sequence[str],
    storage_hints: Sequence[str],
) -> str:
    """Return a hash fingerprint derived from the canonical query dimensions."""

    ns = namespace or "__default__"
    normalized_query = canonicalize_query_text(canonical_query)
    payload = {
        "flags": sorted(hybrid_flags) if hybrid_flags else ["none"],
        "namespace": ns,
        "query": normalized_query,
        "signature": sorted(embedding_signature),
        "storage": sorted(storage_hints) if storage_hints else ["none"],
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return blake2b(serialized.encode("utf-8"), digest_size=16).hexdigest()


def build_cache_key(
    *,
    namespace: str | None,
    backend: str,
    normalized_query: str,
    embedding_signature: Sequence[str],
    embedding_state: str,
    hybrid_flags: Sequence[str],
    storage_hints: Sequence[str],
) -> CacheKey:
    """Return hashed and legacy cache keys for search result caching."""

    ns = namespace or "__default__"
    canonical_query = canonicalize_query_text(normalized_query)
    emb_segment = ",".join(sorted(embedding_signature)) or "__none__"
    flag_segment = ",".join(sorted(hybrid_flags)) if hybrid_flags else "none"
    embedding_state_value = embedding_state or "none"

    legacy = "|".join(
        (
            f"backend={backend}",
            f"query={canonical_query}",
            f"emb_backends={emb_segment}",
            f"embedding={embedding_state_value}",
            f"flags={flag_segment}",
        )
    )

    fingerprint = hash_cache_dimensions(
        namespace=ns,
        canonical_query=canonical_query,
        embedding_signature=embedding_signature,
        hybrid_flags=hybrid_flags,
        storage_hints=storage_hints,
    )

    payload_v3 = {
        "backend": backend,
        "embedding": embedding_state_value,
        "fingerprint": fingerprint,
        "version": 3,
    }
    serialized_v3 = json.dumps(payload_v3, sort_keys=True, separators=(",", ":"))
    digest_v3 = blake2b(serialized_v3.encode("utf-8"), digest_size=16).hexdigest()
    primary = f"v3:{digest_v3}"

    payload_v2 = {
        "backend": backend,
        "embedding": embedding_state_value,
        "flags": sorted(hybrid_flags) if hybrid_flags else ["none"],
        "namespace": ns,
        "query": canonical_query,
        "storage": sorted(storage_hints) if storage_hints else ["none"],
        "signature": sorted(embedding_signature),
    }
    serialized_v2 = json.dumps(payload_v2, sort_keys=True, separators=(",", ":"))
    digest_v2 = blake2b(serialized_v2.encode("utf-8"), digest_size=16).hexdigest()
    alias = f"v2:{digest_v2}"
    aliases = (alias,) if alias != primary else ()

    return CacheKey(primary=primary, legacy=legacy, aliases=aliases, fingerprint=fingerprint)


def canonicalize_query_text(query: str) -> str:
    """Return the canonical representation for query-derived cache keys."""

    collapsed = _WHITESPACE_PATTERN.sub(" ", query.strip())
    return collapsed.lower()


class _SearchCacheView:
    """Lightweight view that scopes cache operations to a namespace."""

    def __init__(self, base: SearchCache, namespace: str) -> None:
        self._base = base
        self._namespace = namespace

    def cache_results(
        self, query: str, backend: str, results: list[dict[str, Any]]
    ) -> None:
        self._base.cache_results(
            query,
            backend,
            results,
            namespace=self._namespace,
        )

    def get_cached_results(
        self, query: str, backend: str
    ) -> list[dict[str, Any]] | None:
        return self._base.get_cached_results(
            query,
            backend,
            namespace=self._namespace,
        )

    def clear(self) -> None:
        self._base.clear(namespace=self._namespace)

    def setup(self, db_path: str | None = None) -> TinyDB:
        return self._base.setup(db_path)

    def teardown(self, remove_file: bool = False) -> None:
        self._base.teardown(remove_file)

    def get_db(self) -> TinyDB:
        return self._base.get_db()

    def namespaced(self, namespace: str | None) -> SearchCache | _SearchCacheView:
        return self._base.namespaced(namespace)

    @property
    def base(self) -> SearchCache:
        """Return the underlying :class:`SearchCache` instance."""

        return self._base

    @property
    def namespace(self) -> str:
        """Return the namespace applied to this view."""

        return self._namespace


_shared_cache = SearchCache()


def get_cache() -> SearchCache:
    """Return the module's shared :class:`SearchCache` instance."""
    return _shared_cache


# ---------------------------------------------------------------------------
# Backwards compatible functional API


def setup(db_path: str | None = None) -> TinyDB:  # pragma: no cover - legacy
    return get_cache().setup(db_path)


def teardown(remove_file: bool = False) -> None:  # pragma: no cover - legacy
    get_cache().teardown(remove_file)


def get_db() -> TinyDB:  # pragma: no cover - legacy
    return get_cache().get_db()


def cache_results(query: str, backend: str, results: list[dict[str, Any]]) -> None:
    get_cache().cache_results(query, backend, results)


def get_cached_results(query: str, backend: str) -> list[dict[str, Any]] | None:
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
