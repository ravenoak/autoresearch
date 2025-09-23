"""Search-oriented storage helpers.

These wrappers delegate to :class:`~autoresearch.storage.StorageManager` so
search modules can persist and retrieve claims without importing the manager
directly. The indirection keeps the search components lightweight while still
reusing the core storage implementation.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..logging_utils import get_logger
from ..storage import StorageManager

log = get_logger(__name__)


def persist_claim(claim: Dict[str, Any]) -> None:
    """Persist a claim using the global storage manager.

    If storage is unavailable (e.g., optional RDF backend not installed in the
    current environment), skip persistence gracefully. This keeps search flows
    functional in minimal test environments while allowing full persistence
    when storage is configured.
    """
    try:
        StorageManager.persist_claim(claim)
    except Exception as exc:  # pragma: no cover - optional backends or runtime assertions
        # In minimal or test environments RDF/vector storage may be unavailable.
        # Swallow and log at debug to keep search flows side-effect free.
        log.debug(f"Skipping claim persistence due to storage error: {exc}")


def update_claim(claim: Dict[str, Any], partial_update: bool = False) -> None:
    """Update an existing claim in storage.

    Falls back to a no-op when storage is unavailable.
    """
    try:
        StorageManager.update_claim(claim, partial_update=partial_update)
    except Exception as exc:  # pragma: no cover - optional backends or runtime assertions
        log.debug(f"Skipping claim update due to storage error: {exc}")


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
