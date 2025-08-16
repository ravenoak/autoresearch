import time
from contextlib import contextmanager

import pytest

from autoresearch import resource_monitor
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory

pytestmark = pytest.mark.slow


class PerfAgent:
    """Minimal agent for performance testing."""

    def __init__(self, name: str, llm_adapter=None) -> None:
        self.name = name

    def can_execute(self, state, config) -> bool:  # pragma: no cover - dummy
        return True

    def execute(self, state, config, adapter=None):  # pragma: no cover - dummy
        adapter("dummy output")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_query_performance(monkeypatch) -> None:
    """Ensure query performance stays within configured limits."""

    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: PerfAgent(name))

    @contextmanager
    def capture(agent_name, metrics, config):
        token_counts = {"in": 0, "out": 0}

        class Adapter:
            def __call__(
                self, prompt: str, model: str | None = None, **kwargs
            ) -> str:
                token_counts["in"] += len(prompt.split())
                token_counts["out"] += 1
                return "ok"

            def generate(
                self, prompt: str, model: str | None = None, **kwargs
            ) -> str:
                return self(prompt, model=model, **kwargs)

        try:
            yield token_counts, Adapter()
        finally:
            metrics.record_tokens(
                agent_name, token_counts["in"], token_counts["out"]
            )

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", capture)

    cfg = ConfigModel(
        agents=["PerfAgent"],
        loops=1,
        llm_backend="dummy",
        token_budget=20,
        ram_budget_mb=200,
    )
    cfg.api.role_permissions["anonymous"] = ["query"]
    cfg.user_preferences["max_latency_seconds"] = 1.0

    get_metrics = getattr(resource_monitor, "get_metrics", resource_monitor._get_usage)

    _, mem_before = get_metrics()
    start = time.perf_counter()
    response = Orchestrator().run_query("performance test query", cfg)
    latency = time.perf_counter() - start
    _, mem_after = get_metrics()

    memory_delta = mem_after - mem_before
    tokens = response.metrics["execution_metrics"]["agent_tokens"]
    total_tokens = sum(v["in"] + v["out"] for v in tokens.values())

    assert latency <= cfg.user_preferences["max_latency_seconds"]
    assert memory_delta <= cfg.ram_budget_mb
    assert cfg.token_budget is None or total_tokens <= cfg.token_budget
