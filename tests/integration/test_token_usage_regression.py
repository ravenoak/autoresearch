"""Regression test for token usage against stored baselines."""

import json
from pathlib import Path

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator

pytestmark = pytest.mark.slow

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_usage.json"
THRESHOLD = 0.10  # allow up to 10% more tokens than baseline


class DummyAgent:
    """Simple agent used for token counting."""

    def __init__(self, name, llm_adapter=None):
        self.name = name

    def can_execute(self, state, config):
        return True

    def execute(self, state, config, adapter=None):  # pragma: no cover - minimal logic
        adapter.generate("hello world")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_token_usage_regression(monkeypatch):
    """Token usage should not grow beyond 10% of the baseline."""

    # Configure orchestrator with a single dummy agent
    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: DummyAgent(name))
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy")
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    response = Orchestrator.run_query("q", cfg)
    tokens = response.metrics["execution_metrics"]["agent_tokens"]
    total_tokens = sum(v.get("in", 0) + v.get("out", 0) for v in tokens.values())

    baseline_total = 0
    if BASELINE_PATH.exists():
        baseline = json.loads(BASELINE_PATH.read_text())
        baseline_total = sum(v.get("in", 0) + v.get("out", 0) for v in baseline.values())
        allowed = baseline_total * (1 + THRESHOLD)
        assert total_tokens <= allowed, (
            f"Total tokens {total_tokens} exceed baseline {baseline_total} by more than 10%"
        )

    BASELINE_PATH.write_text(json.dumps(tokens, indent=2, sort_keys=True))
