import time
from contextlib import contextmanager

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.storage import StorageManager


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
        metrics.setdefault("execution_metrics", {}).setdefault("agent_tokens", {})
        metrics["execution_metrics"]["agent_tokens"][agent_name] = {"in": 0, "out": 0}

        def generate(prompt):
            metrics["execution_metrics"]["agent_tokens"][agent_name]["in"] += len(prompt.split())
            metrics["execution_metrics"]["agent_tokens"][agent_name]["out"] += 1
            return "ok"

        yield (generate, None)

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", capture)

    cfg = ConfigModel(agents=["BenchAgent"], loops=1, llm_backend="dummy")
    cfg.api.role_permissions["anonymous"] = ["query"]

    memory_before = StorageManager._current_ram_mb()
    start = time.perf_counter()
    response = Orchestrator.run_query("q", cfg)
    latency = time.perf_counter() - start
    memory_after = StorageManager._current_ram_mb()

    tokens = response.metrics["execution_metrics"]["agent_tokens"]
    token_baseline(tokens)

    assert latency < 1.0
    assert memory_after - memory_before < 50
