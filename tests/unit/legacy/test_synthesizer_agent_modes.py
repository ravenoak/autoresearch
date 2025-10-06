# mypy: ignore-errors
from __future__ import annotations


from autoresearch.agents.dialectical.synthesizer import SynthesizerAgent
from autoresearch.config.models import ConfigModel
from autoresearch.llm.adapters import LLMAdapter
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.orchestration.state import QueryState


class DummyAdapter(LLMAdapter):
    def __init__(self, output: str) -> None:
        self.output = output

    def generate(self, prompt: str, model: str | None = None, **kwargs) -> str:  # noqa: D401
        """Return preset output regardless of prompt."""
        return self.output


def test_synthesizer_direct_mode() -> None:
    """Synthesizer produces final answer in direct mode."""
    cfg = ConfigModel(reasoning_mode=ReasoningMode.DIRECT)
    agent = SynthesizerAgent(name="Synthesizer", llm_adapter=DummyAdapter("ans"))
    state = QueryState(query="q")
    res = agent.execute(state, cfg)
    assert res["results"]["final_answer"] == "ans"


def test_synthesizer_thesis_and_synthesis() -> None:
    """Synthesizer handles thesis then synthesis in later cycle."""
    cfg = ConfigModel()
    agent = SynthesizerAgent(name="Synthesizer", llm_adapter=DummyAdapter("out"))
    state = QueryState(query="q")
    thesis = agent.execute(state, cfg)
    state.update(thesis)
    state.cycle = 1
    synthesis = agent.execute(state, cfg)
    assert thesis["results"]["thesis"] == "out"
    assert synthesis["results"]["final_answer"] == "out"
