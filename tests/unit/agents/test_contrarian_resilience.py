"""Regression tests for the Contrarian agent."""

from __future__ import annotations

from typing import Any, Mapping, cast

import pytest

from autoresearch.agents.dialectical.contrarian import ContrarianAgent
from autoresearch.config import ConfigModel
from autoresearch.errors import LLMError
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.orchestration.state import QueryState


class _FailingAdapter:
    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        raise LLMError("contrarian failure", model=model)


def _patch_agent(monkeypatch: pytest.MonkeyPatch, agent: ContrarianAgent) -> None:
    monkeypatch.setattr(agent, "get_adapter", lambda config: _FailingAdapter())
    monkeypatch.setattr(agent, "get_model", lambda config: "lmstudio")
    monkeypatch.setattr(
        agent,
        "generate_prompt",
        lambda template, **kwargs: f"tmpl::{kwargs.get('thesis', '')}",
    )


def test_contrarian_handles_llm_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contrarian should record LM errors and emit a fallback antithesis."""

    agent = ContrarianAgent()
    _patch_agent(monkeypatch, agent)

    config = ConfigModel(reasoning_mode=ReasoningMode.DIALECTICAL)
    state = QueryState(query="What is agentic research?")
    state.claims.append({"id": "t1", "type": "thesis", "content": "Agents collaborate"})

    result = agent.execute(state, config)

    metadata = dict(cast(Mapping[str, Any], result["metadata"]))
    assert metadata["phase"].value == "antithesis"
    lm_error = dict(cast(Mapping[str, Any], metadata["lm_error"]))
    assert "contrarian failure" in lm_error["message"]

    results_map = dict(cast(Mapping[str, Any], result["results"]))
    assert results_map["antithesis"].startswith("Antithesis unavailable")
