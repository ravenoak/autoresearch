"""Integration test for token usage tracking against baselines."""

import json
from pathlib import Path

from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.config import ConfigModel, ConfigLoader

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_usage.json"


class DummyAgent:
    """Simple agent that generates a single prompt."""

    def __init__(self, name, llm_adapter=None):
        self.name = name

    def can_execute(self, state, config):
        return True

    def execute(self, state, config, adapter=None):
        adapter.generate("hello world")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_token_usage_matches_baseline(monkeypatch, benchmark):
    """Token counts should match the stored baseline."""

    # Setup a minimal configuration and agent
    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: DummyAgent(name))
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy")
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    def run():
        response = Orchestrator.run_query("q", cfg)
        return response.metrics["execution_metrics"]["agent_tokens"]

    tokens = benchmark.pedantic(run, iterations=1, rounds=1)

    baseline = json.loads(BASELINE_PATH.read_text())
    assert tokens == baseline
