"""Search cache helpers.

These utilities adapt :class:`autoresearch.cache.SearchCache` keys so search
workflows can include namespace, embedding backend, and storage hints in the
underlying TinyDB queries while remaining backwards compatible with legacy
entries.
"""

from __future__ import annotations

from collections.abc import Sequence

from ..cache import CacheKey

_DEFAULT_NAMESPACE = "__default__"
_DEFAULT_EMBEDDING_BACKEND = "__search__"
_DEFAULT_STORAGE_HINT = "none"


def _canonical_namespace(namespace: str | None) -> str:
    """Return a deterministic namespace label for cache routing."""

    return namespace or _DEFAULT_NAMESPACE


def _canonical_embedding_backend(embedding_backend: str | None) -> str:
    """Normalise embedding backend identifiers used in cache slots."""

    return embedding_backend or _DEFAULT_EMBEDDING_BACKEND


def _canonical_storage_hints(storage_hints: Sequence[str] | None) -> tuple[str, ...]:
    """Return a sorted, de-duplicated tuple of storage hints or a placeholder."""

    if not storage_hints:
        return (_DEFAULT_STORAGE_HINT,)

    seen: list[str] = []
    for hint in storage_hints:
        if hint not in seen:
            seen.append(hint)
    return tuple(sorted(seen))


def build_cache_slot(
    candidate: str,
    *,
    namespace: str | None,
    embedding_backend: str | None,
    storage_hints: Sequence[str] | None,
) -> str:
    """Compose a cache slot identifier from the provided metadata."""

    ns = _canonical_namespace(namespace)
    backend_label = _canonical_embedding_backend(embedding_backend)
    storage_label = ",".join(_canonical_storage_hints(storage_hints))
    return f"ns={ns}|embed={backend_label}|storage={storage_label}|{candidate}"


def build_cache_slots(
    cache_key: CacheKey,
    *,
    namespace: str | None,
    embedding_backend: str | None,
    storage_hints: Sequence[str] | None,
) -> tuple[str, ...]:
    """Return cache slot candidates for a :class:`CacheKey` with metadata."""

    return tuple(
        build_cache_slot(
            candidate,
            namespace=namespace,
            embedding_backend=embedding_backend,
            storage_hints=storage_hints,
        )
        for candidate in cache_key.candidates()
    )


__all__ = [
    "build_cache_slot",
    "build_cache_slots",
]
