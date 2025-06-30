import json
from pathlib import Path

from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.config import ConfigModel, ConfigLoader

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_usage_budget.json"


class DummyAgent:
    """Agent that emits a long prompt"""

    def __init__(self, name, llm_adapter=None):
        self.name = name

    def can_execute(self, state, config):
        return True

    def execute(self, state, config, adapter=None):
        adapter.generate("one two three four five six")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_token_usage_budget_regression(monkeypatch):
    """Token usage should respect the configured budget."""

    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: DummyAgent(name))
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy", token_budget=4)
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    response = Orchestrator.run_query("q", cfg)
    tokens = response.metrics["execution_metrics"]["agent_tokens"]

    baseline = json.loads(BASELINE_PATH.read_text())
    assert tokens == baseline
