"""Helpers for re-running claim verification on stored query state."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import BaseModel

from ..agents.dialectical.fact_checker import FactChecker
from ..logging_utils import get_logger
from ..models import QueryResponse
from .state_registry import QueryStateRegistry

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from .state import QueryState

log = get_logger(__name__)


class ReverifyOptions(BaseModel):
    """Parameters controlling re-verification behaviour."""

    broaden_sources: bool = False
    max_results: Optional[int] = None
    max_variations: Optional[int] = None
    prompt_variant: Optional[str] = None

    def to_metadata(self) -> Dict[str, Any]:
        """Serialize options for storage in :class:`QueryState` metadata."""

        payload = self.model_dump(exclude_none=True)
        payload.setdefault("broaden_sources", self.broaden_sources)
        return payload


def _prepare_state_for_reverify(state: "QueryState") -> None:
    """Reset transient fields so claim audits replace prior runs."""

    state.claim_audits = []
    state.claims = [
        dict(claim)
        for claim in state.claims
        if str(claim.get("type", "")).lower() != "verification"
    ]


def run_reverification(
    state_id: str,
    *,
    options: ReverifyOptions | None = None,
) -> QueryResponse:
    """Re-run the FactChecker against a cached :class:`QueryState`.

    Args:
        state_id: Identifier returned by :class:`QueryStateRegistry`.
        options: Optional :class:`ReverifyOptions` overrides.

    Returns:
        Updated :class:`QueryResponse` with refreshed claim audits.

    Raises:
        LookupError: If the requested state is not cached.
    """

    cloned = QueryStateRegistry.clone(state_id)
    if cloned is None:
        raise LookupError(f"No query state registered for id {state_id!r}")
    state, config = cloned
    opts = options or ReverifyOptions()

    _prepare_state_for_reverify(state)
    overrides = opts.to_metadata()
    state.metadata["_reverify_options"] = overrides
    history = state.metadata.setdefault("reverify_history", [])
    history.append({"timestamp": time.time(), "options": dict(overrides)})

    fact_checker = FactChecker()
    try:
        payload = fact_checker.execute(state, config)
    finally:
        state.metadata.pop("_reverify_options", None)

    state.update(payload)
    state.metadata.setdefault("reverify_runs", 0)
    state.metadata["reverify_runs"] += 1
    state.metadata.setdefault("reverify", {})["last_updated"] = time.time()
    state.metadata["reverify"]["last_options"] = overrides

    response = state.synthesize()
    response.state_id = state_id
    QueryStateRegistry.update(state_id, state, config)
    log.info("Reverification completed", extra={"state_id": state_id})
    return response


__all__ = ["ReverifyOptions", "run_reverification"]
