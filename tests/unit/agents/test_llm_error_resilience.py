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
    # Patch class methods for Pydantic models
    def mock_get_adapter(self: Any, config: Any) -> Any:
        return _FailingAdapter()

    def mock_get_model(self: Any, config: Any) -> str:
        return "lmstudio"

    def mock_generate_prompt(self: Any, template: Any, **kwargs: Any) -> str:
        return "prompt payload"

    monkeypatch.setattr(type(agent), "get_adapter", mock_get_adapter)
    monkeypatch.setattr(type(agent), "get_model", mock_get_model)
    monkeypatch.setattr(type(agent), "generate_prompt", mock_generate_prompt)


def test_synthesizer_reports_lm_errors_in_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """Synthesizer should keep the debate alive even when the LLM call fails."""

    agent = SynthesizerAgent(name="test_synthesizer")
    _patch_agent_llm(monkeypatch, agent)

    config = ConfigModel(reasoning_mode=ReasoningMode.DIALECTICAL)
    state = QueryState(query="Test topic")
    state.cycle = 1  # Force synthesis branch
    state.claims.append({"id": "c1", "content": "Existing claim for context"})

    result = agent.execute(state, config)

    assert set(result) >= {"results", "claims", "metadata"}

    results_map = dict(cast(Mapping[str, Any], result["results"]))
    assert results_map["final_answer"].startswith("Synthesis unavailable due to LM error.")
    assert results_map["synthesis"] == "Synthesis unavailable due to LM error."

    claims = cast(list[Mapping[str, Any]], result["claims"])
    assert len(claims) == 1
    claim = dict(claims[0])
    assert claim["type"] == "synthesis"
    assert claim["content"] == "Synthesis unavailable due to LM error."

    lm_errors = cast(list[Mapping[str, Any]], claim["lm_errors"])
    assert len(lm_errors) == 1
    recorded = dict(lm_errors[0])
    assert recorded["phase"] == "synthesis"
    assert recorded["metadata"] is None
    assert "backend rejected prompt" in recorded["message"]

    metadata_map = dict(cast(Mapping[str, Any], result["metadata"]))
    errors_meta = cast(list[Mapping[str, Any]], metadata_map["lm_errors"])
    assert any(error["phase"] == "synthesis" for error in errors_meta)


def test_fact_checker_fallback_includes_error_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FactChecker verification failures should enrich provenance rather than abort."""

    agent = FactChecker(name="test_fact_checker")
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
    assert "backend rejected prompt" in lm_error["message"]


def test_synthesizer_thesis_branch_records_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """First-cycle thesis generation should capture LM errors in metadata."""

    agent = SynthesizerAgent(name="test_synthesizer")
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

    agent = SynthesizerAgent(name="test_synthesizer")
    _patch_agent_llm(monkeypatch, agent)

    config = ConfigModel(reasoning_mode=ReasoningMode.DIRECT)
    state = QueryState(query="Test topic")

    result = agent.execute(state, config)

    results_map = dict(cast(Mapping[str, Any], result["results"]))
    assert results_map["final_answer"].startswith("No answer synthesized due to upstream LM error.")
