from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import reverify as reverify_module
from autoresearch.orchestration.reverify import ReverifyOptions, run_reverification
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.state_registry import QueryStateRegistry
from autoresearch.storage import ClaimAuditStatus
from pydantic import Field


class ConfigWithVerification(ConfigModel):
    """ConfigModel subclass that preserves verification overrides for tests."""

    verification: dict[str, object] = Field(default_factory=dict)


@pytest.fixture(autouse=True)
def _clear_registry() -> Iterator[None]:
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

    def fake_execute(
        self: object, query_state: QueryState, config: ConfigModel
    ) -> dict[str, object]:
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

    module = cast(Any, reverify_module)
    monkeypatch.setattr(module.FactChecker, "execute", fake_execute)

    persisted: list[dict[str, object]] = []

    def record_persist(claim: dict[str, object], partial_update: bool = False) -> None:
        persisted.append({"claim": dict(claim), "partial_update": partial_update})

    monkeypatch.setattr(module.StorageManager, "persist_claim", staticmethod(record_persist))

    monkeypatch.setattr(
        "autoresearch.search.Search.external_lookup",
        lambda *_args: [],
    )

    response = run_reverification(state_id, options=ReverifyOptions(max_retries=2))
    assert isinstance(response, QueryResponse)

    assert len(attempts) == 2, "Reverify should retry until an audit is supported"
    assert persisted, "Claims should be persisted via StorageManager"
    assert all(entry["partial_update"] for entry in persisted)

    extracted_claims: list[dict[str, object]] = []
    for entry in persisted:
        claim_entry = cast(dict[str, object], entry["claim"])
        if claim_entry.get("type") == "extracted":
            extracted_claims.append(claim_entry)
    assert extracted_claims, "An extracted claim should be persisted for reverification"

    assert isinstance(response.metrics, dict)
    metrics = response.metrics.get("reverify", {})
    assert metrics.get("attempts") == 2
    assert metrics.get("retries_used") == 1
    status_counts = metrics.get("claim_status_counts", {})
    assert status_counts.get(ClaimAuditStatus.SUPPORTED.value) == 1
    extraction_meta = metrics.get("extraction", {})
    assert extraction_meta.get("claim_count") == len(extracted_claims)
    assert metrics.get("persisted_claims") == len(persisted)

    assert response.state_id == state_id


def test_reverify_supplies_fact_checker_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Defaults should provide a valid FactChecker configuration."""

    state = QueryState(
        query="default fact checker",
        claims=[{"id": "c-1", "type": "thesis", "content": "Baseline claim"}],
    )
    state_id = QueryStateRegistry.register(state, ConfigModel())

    init_calls: list[dict[str, object]] = []
    execute_calls: list[str] = []

    class DummyFactChecker:
        def __init__(self, **kwargs: object) -> None:
            init_calls.append(dict(kwargs))
            self.enabled = kwargs.get("enabled", True)

        def execute(self, query_state: QueryState, config: ConfigModel) -> dict[str, object]:
            execute_calls.append(query_state.query)
            return {"claims": [], "claim_audits": []}

    module = cast(Any, reverify_module)
    monkeypatch.setattr(module, "FactChecker", DummyFactChecker)
    monkeypatch.setattr(
        module.StorageManager,
        "persist_claim",
        staticmethod(lambda claim, partial_update=False: None),
    )

    response = run_reverification(state_id)
    assert isinstance(response, QueryResponse)

    assert init_calls, "FactChecker should be constructed with defaults"
    assert init_calls[0]["name"] == "FactChecker"
    assert init_calls[0]["enabled"] is True
    assert execute_calls == ["default fact checker"]
    assert isinstance(response.metrics, dict)
    metrics = response.metrics.get("reverify", {})
    assert metrics.get("attempts") == 1


def test_reverify_respects_fact_checker_opt_out(monkeypatch: pytest.MonkeyPatch) -> None:
    """Opting out via configuration should skip FactChecker execution."""

    state = QueryState(
        query="skip fact checker",
        claims=[{"id": "c-2", "type": "thesis", "content": "Skip claim"}],
    )
    config = ConfigWithVerification(
        verification={"fact_checker": {"enabled": False, "name": "FactChecker"}}
    )
    state_id = QueryStateRegistry.register(state, config)

    init_calls: list[dict[str, object]] = []

    class DisabledFactChecker:
        def __init__(self, **kwargs: object) -> None:
            init_calls.append(dict(kwargs))
            self.enabled = False

        def execute(self, query_state: QueryState, config: ConfigModel) -> dict[str, object]:
            raise AssertionError("FactChecker should not execute when disabled")

    module = cast(Any, reverify_module)
    monkeypatch.setattr(module, "FactChecker", DisabledFactChecker)
    persist_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        module.StorageManager,
        "persist_claim",
        staticmethod(lambda claim, partial_update=False: persist_calls.append(dict(claim))),
    )

    response = run_reverification(state_id)
    assert isinstance(response, QueryResponse)

    assert not init_calls, "FactChecker should not be constructed when disabled"
    assert not persist_calls, "No claims should be persisted when fact checking is skipped"
    assert isinstance(response.metrics, dict)
    metrics = response.metrics.get("reverify", {})
    assert metrics.get("skipped") == "fact_checker_disabled"
    assert metrics.get("attempts") == 0
    assert metrics.get("retries_used") == 0
