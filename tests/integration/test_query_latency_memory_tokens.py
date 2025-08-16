import time
from contextlib import contextmanager

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.storage import StorageManager

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class BenchAgent:
    def __init__(self, name: str, llm_adapter=None):
        self.name = name

    def can_execute(self, state, config):  # pragma: no cover - dummy
        return True

    def execute(self, state, config, adapter=None):
        adapter("benchmark prompt")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_query_latency_memory_tokens(monkeypatch, token_baseline):
    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: BenchAgent(name))

    @contextmanager
    def capture(agent_name, metrics, config):
        def generate(prompt):
            metrics.record_tokens(agent_name, len(prompt.split()), 1)
            return "ok"

        yield ({}, generate)

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", capture)

    cfg = ConfigModel(agents=["BenchAgent"], loops=1, llm_backend="dummy")
    cfg.api.role_permissions["anonymous"] = ["query"]

    memory_before = StorageManager._current_ram_mb()
    start = time.perf_counter()
    response = Orchestrator().run_query("q", cfg)
    latency = time.perf_counter() - start
    memory_after = StorageManager._current_ram_mb()

    tokens = response.metrics["execution_metrics"]["agent_tokens"]
    token_baseline(tokens)

    assert latency < 1.0
    assert memory_after - memory_before < 50
