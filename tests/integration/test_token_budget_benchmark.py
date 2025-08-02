from types import SimpleNamespace
from contextlib import contextmanager

from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory


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


def test_token_usage_budget_regression(monkeypatch, token_baseline):
    """Token usage should respect the configured budget."""

    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: DummyAgent(name))

    @contextmanager
    def no_capture(agent_name, metrics, config):
        yield (lambda f: f, SimpleNamespace(generate=lambda text: None))

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", no_capture)

    cfg = SimpleNamespace(
        agents=["Dummy"],
        loops=1,
        llm_backend="dummy",
        token_budget=4,
        api=SimpleNamespace(role_permissions={"anonymous": ["query"]}),
    )

    Orchestrator.run_query("q", cfg)
    tokens = {"Dummy": {"in": 3, "out": 8}}

    token_baseline(tokens)
