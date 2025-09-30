from __future__ import annotations

from typing import Any

import pytest

from autoresearch.output_format import OutputDepth, OutputFormatter
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import ClaimAuditStatus


@pytest.fixture()
def unsupported_state(monkeypatch: pytest.MonkeyPatch) -> QueryState:
    """Provide a QueryState with an unsupported claim for audit testing."""

    def fake_external_lookup(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "title": "Placeholder evidence",
                "snippet": "No corroborating evidence for the unsupported claim.",
                "url": "https://example.com/unsupported",
            }
        ]

    monkeypatch.setattr(
        "autoresearch.search.Search.external_lookup",
        fake_external_lookup,
    )

    return QueryState(
        query="unsupported audit rehearsal",
        results={"final_answer": "Original answer without hedging."},
        claims=[
            {
                "id": "c1",
                "type": "synthesis",
                "content": "The system guarantees an unverified capability.",
            }
        ],
        claim_audits=[
            {
                "claim_id": "c1",
                "status": ClaimAuditStatus.UNSUPPORTED.value,
                "entailment_score": 0.05,
            }
        ],
    )


def test_answer_auditor_hedges_unsupported_claims(unsupported_state: QueryState) -> None:
    """Answer auditing should hedge unsupported claims and update provenance."""

    response = unsupported_state.synthesize()

    assert response.answer.startswith("⚠️"), "Answer should be prefixed with a caution symbol"
    assert response.metrics["answer_audit"]["unsupported_claims"] == ["c1"]

    reasoning = response.reasoning[0]
    assert reasoning.get("hedged_content", "").startswith("⚠️ Unsupported")
    audit_entries = [
        audit for audit in response.claim_audits if audit.get("claim_id") == "c1"
    ]
    assert any(
        audit.get("provenance", {}).get("retrieval", {}).get("mode")
        == "answer_audit.retry"
        for audit in audit_entries
    )

    depth_payload = OutputFormatter.plan_response_depth(response, OutputDepth.CONCISE)
    assert all(
        "unverified capability" not in finding.lower()
        for finding in depth_payload.key_findings
    )
    assert "unsupported claims" in depth_payload.notes.get("key_findings", "").lower()
