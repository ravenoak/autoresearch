import json
import importlib.util
from pathlib import Path

import pytest

from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.search import Search
from autoresearch.storage import StorageManager

pytestmark = pytest.mark.slow

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_token_memory.py"
spec = importlib.util.spec_from_file_location("benchmark_token_memory", SCRIPT_PATH)
benchmark_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(benchmark_module)  # type: ignore
run_benchmark = benchmark_module.run_benchmark

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_memory.json"
BUDGET_BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_usage_budget.json"


class DummyAgent:
    """Minimal agent used for benchmarks."""

    def __init__(self, name: str, llm_adapter=None) -> None:
        self.name = name

    def can_execute(self, state, config) -> bool:  # pragma: no cover - dummy
        return True

    def execute(self, state, config, adapter=None):  # pragma: no cover - dummy
        adapter.generate("one two three four five six")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_query_performance_memory_tokens(benchmark):
    """Benchmark query processing and verify memory and token usage."""

    # Setup
    query = "performance benchmark"
    memory_before = StorageManager._current_ram_mb()

    def run():
        Search.generate_queries(query)

    # Execute
    benchmark(run)
    metrics = run_benchmark()
    memory_after = StorageManager._current_ram_mb()

    # Verify
    baseline = json.loads(BASELINE_PATH.read_text())
    assert metrics["tokens"] == baseline["tokens"]
    assert metrics["memory_delta_mb"] <= baseline["memory_delta_mb"] + 5
    assert memory_after - memory_before < 10


def test_token_budget_limit(monkeypatch):
    """Token usage should respect the configured budget."""

    # Setup
    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: DummyAgent(name))
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy", token_budget=4)
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    # Execute
    response = Orchestrator.run_query("q", cfg)
    tokens = response.metrics["execution_metrics"]["agent_tokens"]

    # Verify
    baseline = json.loads(BUDGET_BASELINE_PATH.read_text())
    assert tokens == baseline
