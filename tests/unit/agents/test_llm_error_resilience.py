"""Behavioural tests covering agent resilience to LLM errors."""

from __future__ import annotations

from typing import Any, Mapping, cast

import pytest

from autoresearch.agents.dialectical.fact_checker import FactChecker
from autoresearch.agents.dialectical.synthesizer import SynthesizerAgent
from autoresearch.config import ConfigModel
from autoresearch.errors import LLMError
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.orchestration.state import QueryState


class _FailingAdapter:
    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        raise LLMError("backend rejected prompt", model=model, suggestion="retry later")


def _patch_agent_llm(monkeypatch: pytest.MonkeyPatch, agent: Any) -> None:
    monkeypatch.setattr(agent, "get_adapter", lambda config: _FailingAdapter())
    monkeypatch.setattr(agent, "get_model", lambda config: "lmstudio")
    monkeypatch.setattr(agent, "generate_prompt", lambda template, **kwargs: "prompt payload")


def test_synthesizer_reports_lm_errors_in_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """Synthesizer should keep the debate alive even when the LLM call fails."""

    agent = SynthesizerAgent()
    _patch_agent_llm(monkeypatch, agent)

    config = ConfigModel(reasoning_mode=ReasoningMode.DIALECTICAL)
    state = QueryState(query="Test topic")
    state.cycle = 1  # Force synthesis branch
    state.claims.append({"id": "c1", "content": "Existing claim for context"})

    result = agent.execute(state, config)

    results_map = dict(cast(Mapping[str, Any], result["results"]))
    assert results_map["final_answer"].startswith("Synthesis unavailable due to LM error.")

    claims = cast(list[Mapping[str, Any]], result["claims"])
    claim_metadata = dict(cast(Mapping[str, Any], claims[0].get("metadata", {})))
    lm_errors = cast(list[Mapping[str, Any]], claim_metadata["lm_errors"])
    recorded = dict(lm_errors[0])
    assert recorded["phase"] == "synthesis"
    assert "backend rejected prompt" in recorded["message"]


def test_fact_checker_fallback_includes_error_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FactChecker verification failures should enrich provenance rather than abort."""

    agent = FactChecker()
    _patch_agent_llm(monkeypatch, agent)
    monkeypatch.setattr(
        "autoresearch.agents.dialectical.fact_checker.Search.external_lookup",
        lambda *args, **kwargs: [{"snippet": "Existing claim for context"}],
    )

    config = ConfigModel(reasoning_mode=ReasoningMode.DIALECTICAL)
    state = QueryState(query="Test topic")
    state.claims.append({"id": "c1", "content": "Existing claim for context"})

    result = agent.execute(state, config)

    results_map = dict(cast(Mapping[str, Any], result["results"]))
    verification = cast(str, results_map["verification"])
    assert "Verification unavailable: the LLM backend rejected the request" in verification

    metadata_map = dict(cast(Mapping[str, Any], result["metadata"]))
    provenance = dict(cast(Mapping[str, Any], metadata_map["audit_provenance_fact_checker"]))
    lm_error = dict(cast(Mapping[str, Any], provenance["lm_error"]))
    assert lm_error["message"] == "backend rejected prompt"


def test_synthesizer_thesis_branch_records_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """First-cycle thesis generation should capture LM errors in metadata."""

    agent = SynthesizerAgent()
    _patch_agent_llm(monkeypatch, agent)

    config = ConfigModel(reasoning_mode=ReasoningMode.DIALECTICAL)
    state = QueryState(query="Test topic")
    state.cycle = 0  # trigger thesis branch

    result = agent.execute(state, config)

    metadata_map = dict(cast(Mapping[str, Any], result["metadata"]))
    lm_errors = cast(list[Mapping[str, Any]], metadata_map["lm_errors"])
    assert lm_errors[0]["phase"] == "thesis"


def test_synthesizer_direct_mode_returns_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Direct reasoning mode should still emit a fallback answer when the LM fails."""

    agent = SynthesizerAgent()
    _patch_agent_llm(monkeypatch, agent)

    config = ConfigModel(reasoning_mode=ReasoningMode.DIRECT)
    state = QueryState(query="Test topic")

    result = agent.execute(state, config)

    results_map = dict(cast(Mapping[str, Any], result["results"]))
    assert results_map["final_answer"].startswith("No answer synthesized due to upstream LM error.")
