"""Regression tests for structured answer audit warnings."""

from __future__ import annotations

from typing import Any

import pytest

from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import AnswerAuditor, QueryState
from autoresearch.output_format import OutputDepth, OutputFormatter
from autoresearch.storage import ClaimAuditStatus


def _make_state(
    *,
    answer: str,
    claim_status: ClaimAuditStatus,
    claim_id: str = "c1",
    claim_text: str = "Unverified capability",
) -> QueryState:
    """Create a query state containing a single audited claim."""

    state = QueryState(query="structured warnings smoke test")
    state.results["final_answer"] = answer
    state.claims.append({
        "id": claim_id,
        "content": claim_text,
        "audit": {"claim_id": claim_id, "status": claim_status.value},
    })
    state.claim_audits.append(
        {
            "claim_id": claim_id,
            "status": claim_status.value,
            "entailment": 0.1,
        }
    )
    return state


def _first_warning_entry(response: QueryResponse) -> dict[str, Any]:
    warnings = response.warnings
    assert warnings, "Expected warnings to be present in the response"
    return warnings[0]


def test_answer_audit_preserves_answer_and_emits_warnings() -> None:
    """Unsupported claims should produce structured warnings without hedging."""

    state = _make_state(answer="Original answer", claim_status=ClaimAuditStatus.UNSUPPORTED)
    outcome = AnswerAuditor(state).review()

    assert outcome.answer == "Original answer"
    assert outcome.warnings, "Warnings were not emitted for unsupported claim"
    warning = outcome.warnings[0]
    assert warning["code"] == "answer_audit.unsupported_claims"
    assert warning["claims"]
    assert warning["claims"][0]["id"] == "c1"
    assert "Unsupported" in warning["message"]

    response = state.synthesize()
    assert response.answer == "Original answer"
    assert response.warnings == outcome.warnings
    audit_metrics = response.metrics.get("answer_audit", {})
    assert audit_metrics.get("warnings") == outcome.warnings


def test_answer_audit_needs_review_warning() -> None:
    """Needs review claims should surface a dedicated warning entry."""

    state = _make_state(answer="Review answer", claim_status=ClaimAuditStatus.NEEDS_REVIEW)
    outcome = AnswerAuditor(state).review()

    assert outcome.answer == "Review answer"
    assert outcome.warnings
    warning = outcome.warnings[0]
    assert warning["code"] == "answer_audit.needs_review_claims"
    assert warning["claims"][0]["id"] == "c1"


def test_output_formatter_uses_structured_warnings() -> None:
    """Depth payloads should surface caution notes while preserving the answer."""

    state = _make_state(answer="CLI answer", claim_status=ClaimAuditStatus.UNSUPPORTED)
    response = state.synthesize()
    warning = _first_warning_entry(response)
    assert warning["claims"]

    depth_payload = OutputFormatter.plan_response_depth(response, OutputDepth.TLDR)
    assert depth_payload.answer == "CLI answer"
    note = depth_payload.notes.get("tldr", "")
    assert "unsupported" in note.lower()
    assert "cli answer" not in note.lower()


def test_answer_audit_retry_handles_equal_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression test for sorting retries when entailment scores are tied."""

    state = QueryState(query="tie breaker")
    state.claims.append({"id": "c1", "content": "Autoresearch improves workflows"})

    monkeypatch.setattr(
        "autoresearch.orchestration.state.Search.external_lookup",
        lambda *args, **kwargs: [
            {"snippet": "Autoresearch improves workflows"},
            {"snippet": "Autoresearch improves workflows"},
        ],
    )

    auditor = AnswerAuditor(state)
    retry = auditor._retry_claim(state.claims[0], [])
    assert retry is not None
    assert retry.sources
