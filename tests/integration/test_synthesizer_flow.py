from __future__ import annotations

import pytest

from autoresearch.agents.dialectical.synthesizer import SynthesizerAgent
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.state import QueryState


class DummyAdapter:
    def generate(self, prompt: str, model: str | None = None) -> str:  # noqa: D401
        """Provide deterministic output for integration tests."""
        return "integration"


@pytest.mark.slow
def test_synthesizer_integration_cycle() -> None:
    """Run synthesizer across cycles and update QueryState."""
    cfg = ConfigModel()
    agent = SynthesizerAgent(name="Synthesizer", llm_adapter=DummyAdapter())
    state = QueryState(query="q")

    first = agent.execute(state, cfg)
    state.update(first)
    state.cycle = 1
    second = agent.execute(state, cfg)
    state.update(second)

    assert state.results["final_answer"] == "integration"
    assert any(c.get("type") == "thesis" for c in state.claims)
