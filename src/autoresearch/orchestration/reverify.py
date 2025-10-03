"""Helpers for re-running claim verification on stored query state."""

from __future__ import annotations

import time
from collections import Counter
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional
from uuid import uuid4

from pydantic import BaseModel

from ..agents.dialectical.fact_checker import FactChecker
from ..errors import StorageError
from ..evidence import extract_candidate_claims, should_retry_verification
from ..logging_utils import get_logger
from ..models import QueryResponse
from ..storage import StorageManager
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
    max_retries: int = 1
    retry_backoff: float = 0.0
    max_claims: Optional[int] = None

    def to_metadata(self) -> Dict[str, Any]:
        """Serialize options for storage in :class:`QueryState` metadata."""

        payload = self.model_dump(exclude_none=True)
        payload.setdefault("broaden_sources", self.broaden_sources)
        payload.setdefault("max_retries", self.max_retries)
        payload.setdefault("retry_backoff", self.retry_backoff)
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
    reverify_meta = state.metadata.setdefault("reverify", {})

    base_claims = [dict(claim) for claim in state.claims]
    extracted_claims: list[str] = []
    if not base_claims:
        answer_text = ""
        if isinstance(state.results, Mapping):
            answer_text = str(state.results.get("final_answer") or "")
        if not answer_text:
            answer_text = str(state.metadata.get("final_answer") or "")
        max_claims = opts.max_claims if opts.max_claims is not None else 8
        extracted_claims = extract_candidate_claims(answer_text, max_claims=max_claims)
        for content in extracted_claims:
            claim_payload = {
                "id": f"reverify:{uuid4()}",
                "type": "extracted",
                "content": content,
                "origin": "reverify.extracted",
            }
            state.claims.append(claim_payload)
        base_claims = [dict(claim) for claim in state.claims]

    reverify_meta["seed_claims"] = len(base_claims)
    if extracted_claims:
        reverify_meta["extraction"] = {
            "source": "results.final_answer",
            "claim_count": len(extracted_claims),
        }

    max_retries = max(1, int(opts.max_retries))
    backoff = max(0.0, float(opts.retry_backoff))
    attempts = 0
    aggregated_audits: list[dict[str, Any]] = []

    fact_checker = FactChecker()
    try:
        while attempts < max_retries:
            attempts += 1
            start = time.time()
            payload = fact_checker.execute(state, config)
            duration = time.time() - start
            state.update(payload)
            aggregated_audits = list(state.claim_audits)
            history.append(
                {
                    "timestamp": time.time(),
                    "options": dict(overrides),
                    "attempt": attempts,
                    "duration": duration,
                    "audit_count": len(payload.get("claim_audits") or []),
                }
            )
            if not should_retry_verification(aggregated_audits):
                break
            if attempts >= max_retries:
                break
            log.info(
                "Reverification retry scheduled",
                extra={
                    "state_id": state_id,
                    "attempt": attempts,
                    "max_retries": max_retries,
                },
            )
            _prepare_state_for_reverify(state)
            state.claims = [dict(claim) for claim in base_claims]
            if backoff > 0.0:
                time.sleep(backoff)
    finally:
        state.metadata.pop("_reverify_options", None)

    state.metadata.setdefault("reverify_runs", 0)
    state.metadata["reverify_runs"] += 1
    reverify_meta["last_updated"] = time.time()
    reverify_meta["last_options"] = overrides
    reverify_meta["attempts"] = attempts
    reverify_meta["retries_used"] = max(0, attempts - 1)

    if aggregated_audits:
        status_counts = Counter(
            str(audit.get("status") or "needs_review") for audit in aggregated_audits
        )
        reverify_meta["claim_status_counts"] = dict(status_counts)
        reverify_meta["audit_count"] = len(aggregated_audits)
    else:
        reverify_meta["audit_count"] = 0

    persisted = 0
    persist_failures: list[str] = []
    for claim in state.claims:
        if not isinstance(claim, Mapping):
            continue
        claim_payload = dict(claim)
        claim_id = str(claim_payload.get("id") or "")
        if not claim_id:
            continue
        try:
            StorageManager.persist_claim(claim_payload, partial_update=True)
            persisted += 1
        except (StorageError, ValueError) as exc:
            persist_failures.append(claim_id)
            log.warning(
                "Failed to persist claim during reverification",
                extra={"state_id": state_id, "claim_id": claim_id, "error": str(exc)},
            )

    if persisted:
        reverify_meta["persisted_claims"] = persisted
    if persist_failures:
        reverify_meta["persist_failures"] = persist_failures

    response = state.synthesize()
    response.state_id = state_id
    QueryStateRegistry.update(state_id, state, config)
    log.info("Reverification completed", extra={"state_id": state_id})
    return response


__all__ = ["ReverifyOptions", "run_reverification"]
