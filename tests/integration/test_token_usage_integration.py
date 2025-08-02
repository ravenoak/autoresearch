"""Integration test for token usage tracking against baselines."""

import json
import os
from pathlib import Path

from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_usage.json"
# Allow tokens to exceed the baseline by this many tokens before failing
THRESHOLD = int(os.getenv("TOKEN_USAGE_THRESHOLD", "0"))


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


def test_token_usage_matches_baseline(monkeypatch):
    """Token counts should match the stored baseline."""

    # Setup a minimal configuration and agent
    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: DummyAgent(name))
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy")
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    response = Orchestrator.run_query("q", cfg)
    tokens = response.metrics["execution_metrics"]["agent_tokens"]

    baseline = json.loads(BASELINE_PATH.read_text())
    assert tokens.keys() == baseline.keys()
    for agent, counts in baseline.items():
        measured = tokens[agent]
        assert measured["in"] <= counts["in"] + THRESHOLD, (
            f"Inbound tokens for {agent} exceed baseline by more than {THRESHOLD}"
        )
        assert measured["out"] <= counts["out"] + THRESHOLD, (
            f"Outbound tokens for {agent} exceed baseline by more than {THRESHOLD}"
        )
