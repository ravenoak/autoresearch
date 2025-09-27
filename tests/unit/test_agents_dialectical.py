"""Unit tests covering dialectical agents' claim audit provenance."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from autoresearch.agents.dialectical.fact_checker import FactChecker
from autoresearch.agents.dialectical.synthesizer import SynthesizerAgent
from autoresearch.config.models import ConfigModel
from autoresearch.llm.adapters import LLMAdapter
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.orchestration.state import QueryState


class _DummyAdapter(LLMAdapter):
    """Minimal adapter stub that returns deterministic completions."""

    available_models = ["mock-model"]

    def generate(self, prompt: str, model: str | None = None, **_: Any) -> str:
        return "analysis"

    def validate_model(self, model: str | None) -> str:
        return model or self.available_models[0]


@pytest.fixture()
def adapter() -> _DummyAdapter:
    return _DummyAdapter()


def test_fact_checker_audit_provenance(adapter: _DummyAdapter, monkeypatch: pytest.MonkeyPatch) -> None:
    """FactChecker should emit provenance-rich audits with stable source ids."""

    def fake_lookup(*args: Any, **_: Any):
        if len(args) == 1:
            query = args[0]
        else:
            query = args[1]
        assert query  # query should always be provided
        return [
            {
                "title": "Evidence",
                "url": "https://example.com/evidence",
                "snippet": "Solar energy reduces emissions.",
            }
        ]

    monkeypatch.setattr(
        "autoresearch.agents.dialectical.fact_checker.Search.external_lookup",
        fake_lookup,
    )

    state = QueryState(
        query="solar energy benefits",
        claims=[{"id": "claim-1", "content": "Solar energy reduces emissions."}],
    )
    cfg = ConfigModel.model_construct()
    agent = FactChecker(name="FactChecker", llm_adapter=adapter)

    with patch.object(FactChecker, "get_model", return_value="mock-model"):
        result = agent.execute(state, cfg)

    assert result["claim_audits"], "claim audits should be emitted"
    audit = result["claim_audits"][0]
    assert audit["provenance"]["retrieval"]["base_query"] == "solar energy benefits"
    assert audit["provenance"]["evidence"]["best_source_id"]
    assert audit["provenance"]["retrieval"]["events"], "retrieval events should be logged"
    for source in result["sources"]:
        assert "source_id" in source

    claim_audit = result["claims"][0]["audit"]
    assert claim_audit["provenance"]["evidence"]["top_source_ids"], (
        "top source ids should be tracked"
    )
    per_claim = claim_audit["provenance"]["backoff"]["per_claim"]
    assert per_claim["claim-1"]["retry_count"] == 0
    assert "paraphrases" in per_claim["claim-1"]
    assert claim_audit["provenance"]["backoff"]["total_retries"] == 0


def test_synthesizer_support_audit_provenance(adapter: _DummyAdapter) -> None:
    """Synthesizer support audits should thread provenance into payloads."""

    state = QueryState(
        query="climate mitigation",
        claims=[
            {"id": "claim-1", "type": "thesis", "content": "Solar energy reduces emissions."},
            {"id": "claim-2", "type": "antithesis", "content": "Wind energy is renewable."},
        ],
        cycle=1,
    )
    cfg = ConfigModel.model_construct(reasoning_mode=ReasoningMode.DIALECTICAL)
    agent = SynthesizerAgent(name="Synthesizer", llm_adapter=adapter)

    with patch.object(SynthesizerAgent, "get_model", return_value="mock-model"):
        result = agent.execute(state, cfg)

    audits = {audit["claim_id"]: audit for audit in result["claim_audits"]}
    support_audit = audits["claim-1"]
    assert support_audit["provenance"]["retrieval"]["mode"] == "hypothesis_vs_claim"
    assert support_audit["provenance"]["evidence"]["source_ids"], (
        "support source ids should be present"
    )

    claim = result["claims"][0]
    summary_audit = audits[claim["id"]]
    support_ids = summary_audit["provenance"]["evidence"]["support_audit_ids"]
    assert support_ids, "summary audit should reference support audits"
    assert audits["claim-1"]["audit_id"] in support_ids
    assert summary_audit["provenance"]["retrieval"]["mode"] == "peer_consensus"
