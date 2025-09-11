"""Search-oriented storage helpers.

These wrappers delegate to :class:`~autoresearch.storage.StorageManager` so
search modules can persist and retrieve claims without importing the manager
directly. The indirection keeps the search components lightweight while still
reusing the core storage implementation.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..storage import StorageManager


def persist_claim(claim: Dict[str, Any]) -> None:
    """Persist a claim using the global storage manager."""
    StorageManager.persist_claim(claim)


def update_claim(claim: Dict[str, Any], partial_update: bool = False) -> None:
    """Update an existing claim in storage."""
    StorageManager.update_claim(claim, partial_update=partial_update)


def get_claim(claim_id: str) -> Optional[Dict[str, Any]]:
    """Return a persisted claim if available."""
    try:
        return StorageManager.get_claim(claim_id)
    except Exception:  # pragma: no cover - lookup may raise
        return None


def vector_search(embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
    """Search persisted claims by embedding similarity."""
    return StorageManager.vector_search(embedding, k=k)


def persist_results(results: Iterable[Dict[str, Any]]) -> None:
    """Persist ranked search results as claims.

    Each result is converted into a minimal claim containing an ``id`` and
    ``content``. Existing claims are updated if they already exist.
    """
    for r in results:
        claim_id = r.get("url")
        if not claim_id:
            continue
        claim = {
            "id": claim_id,
            "type": "fact",
            "content": r.get("snippet") or r.get("title") or "",
            "embedding": r.get("embedding"),
        }
        persist_claim(claim)
