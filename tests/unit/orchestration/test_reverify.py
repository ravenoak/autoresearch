from __future__ import annotations

from typing import Any

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import reverify as reverify_module
from autoresearch.orchestration.reverify import ReverifyOptions, run_reverification
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.state_registry import QueryStateRegistry
from autoresearch.storage import ClaimAuditStatus


@pytest.fixture(autouse=True)
def _clear_registry() -> None:
    """Reset the in-memory state registry before and after each test."""

    QueryStateRegistry._store.clear()
    yield
    QueryStateRegistry._store.clear()


def test_reverify_extracts_claims_and_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reverification should extract claims, retry audits, and persist updates."""

    state = QueryState(
        query="accuracy audit",
        results={"final_answer": "Autoresearch reports 92 percent accuracy on regression sweeps."},
    )
    state_id = QueryStateRegistry.register(state, ConfigModel())

    attempts: list[ClaimAuditStatus] = []

    def fake_execute(query_state: QueryState, config: ConfigModel) -> dict[str, Any]:
        base_claims = [
            claim
            for claim in query_state.claims
            if str(claim.get("type", "")) != "verification"
        ]
        assert base_claims, "Reverify should seed claims before executing the fact checker"
        claim_id = str(base_claims[0]["id"])
        status = ClaimAuditStatus.NEEDS_REVIEW if not attempts else ClaimAuditStatus.SUPPORTED
        attempts.append(status)
        verification_claim = {
            "id": f"verification-{len(attempts)}",
            "type": "verification",
            "content": "Checked claims",
        }
        audit_payload = {
            "claim_id": claim_id,
            "status": status.value,
            "sample_size": 0 if status is ClaimAuditStatus.NEEDS_REVIEW else 2,
            "entailment_score": 0.78 if status is ClaimAuditStatus.SUPPORTED else None,
        }
        return {"claims": [verification_claim], "claim_audits": [audit_payload]}

    monkeypatch.setattr(
        reverify_module.FactChecker,
        "execute",
        fake_execute,
    )

    persisted: list[dict[str, Any]] = []

    def record_persist(claim: dict[str, Any], partial_update: bool = False) -> None:
        persisted.append({"claim": dict(claim), "partial_update": partial_update})

    monkeypatch.setattr(
        reverify_module.StorageManager,
        "persist_claim",
        staticmethod(record_persist),
    )

    monkeypatch.setattr(
        "autoresearch.search.Search.external_lookup",
        lambda *args, **kwargs: [],
    )

    response = run_reverification(state_id, options=ReverifyOptions(max_retries=2))

    assert len(attempts) == 2, "Reverify should retry until an audit is supported"
    assert persisted, "Claims should be persisted via StorageManager"
    assert all(entry["partial_update"] for entry in persisted)

    extracted_claims = [
        entry["claim"]
        for entry in persisted
        if entry["claim"].get("type") == "extracted"
    ]
    assert extracted_claims, "An extracted claim should be persisted for reverification"

    metrics = response.metrics.get("reverify", {})
    assert metrics.get("attempts") == 2
    assert metrics.get("retries_used") == 1
    status_counts = metrics.get("claim_status_counts", {})
    assert status_counts.get(ClaimAuditStatus.SUPPORTED.value) == 1
    extraction_meta = metrics.get("extraction", {})
    assert extraction_meta.get("claim_count") == len(extracted_claims)
    assert metrics.get("persisted_claims") == len(persisted)

    assert response.state_id == state_id
