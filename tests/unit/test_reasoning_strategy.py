from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.reasoning import ChainOfThoughtStrategy
import pytest


class DummySynth:
    def __init__(self):
        self.calls = 0

    def can_execute(self, state, config):
        return True

    def execute(self, state, config):
        self.calls += 1
        return {"results": {"final_answer": f"step-{self.calls}"}}


def test_chain_of_thought_strategy_loops(monkeypatch: pytest.MonkeyPatch) -> None:
    synth = DummySynth()
    monkeypatch.setattr(
        "autoresearch.agents.registry.AgentFactory.get",
        lambda name: synth,
    )
    cfg = ConfigModel(loops=2)
    strategy = ChainOfThoughtStrategy()
    resp = strategy.run_query("q", cfg)
    assert synth.calls == 2
    assert resp.answer == "step-2"
    metrics = resp.metrics.get("execution_metrics", {})
    assert metrics.get("cycles_completed") == 2
