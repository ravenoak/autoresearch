from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
from typing import Callable, Mapping

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from tests.optional_imports import import_or_skip

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import orchestrator as orch_mod
from autoresearch.orchestration.state import QueryState
from tests.analysis.distributed_coordination_analysis import simulate

Orchestrator = orch_mod.Orchestrator
AgentFactory = orch_mod.AgentFactory
StorageManager = orch_mod.StorageManager


class Search:
    @staticmethod
    def generate_queries(query: str) -> list[str]:  # pragma: no cover - simple stub
        return [query]


pytestmark = [pytest.mark.slow, pytest.mark.integration]

import_or_skip("pytest_benchmark")

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_token_memory.py"
spec = importlib.util.spec_from_file_location("benchmark_token_memory", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load benchmark_token_memory module")
benchmark_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark_module)
run_benchmark: Callable[[], dict[str, object]] = benchmark_module.run_benchmark

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_memory.json"


class DummyAgent:
    """Minimal agent used for benchmarks."""

    def __init__(
        self,
        name: str,
        llm_adapter: Callable[[str], object] | None = None,
    ) -> None:
        self.name = name

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:  # pragma: no cover - dummy
        return True

    def execute(
        self,
        state: QueryState,
        config: ConfigModel,
        adapter: Callable[..., str] | None = None,
    ) -> dict[str, dict[str, str]]:  # pragma: no cover - dummy
        if adapter is None:
            raise AssertionError("adapter must be provided")
        adapter.generate("one two three four five six")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_query_performance_memory_tokens(
    benchmark: BenchmarkFixture,
    token_baseline: Callable[[dict[str, dict[str, int]], int], None],
) -> None:
    """Benchmark query processing and verify memory and token usage."""

    # Setup
    query = "performance benchmark"
    memory_before = StorageManager._current_ram_mb()

    def run() -> None:
        Search.generate_queries(query)

    # Execute
    benchmark(run)
    metrics: Mapping[str, object] = run_benchmark()
    memory_after = StorageManager._current_ram_mb()

    # Verify
    baseline = json.loads(BASELINE_PATH.read_text())
    token_baseline(metrics["tokens"])
    assert float(metrics["memory_delta_mb"]) <= baseline["memory_delta_mb"] + 5
    assert memory_after - memory_before < 10


def _build_dummy_agent(
    name: str, llm_adapter: Callable[[str], object] | None = None
) -> DummyAgent:
    return DummyAgent(name)


def test_token_budget_limit(
    monkeypatch: pytest.MonkeyPatch,
    token_baseline: Callable[[dict[str, dict[str, int]], int], None],
) -> None:
    """Token usage should respect the configured budget."""

    # Setup
    monkeypatch.setattr(AgentFactory, "get", _build_dummy_agent)
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy", token_budget=4)
    cfg.api.role_permissions["anonymous"] = ["query"]
    
    def _load_config_stub(self: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", _load_config_stub)
    ConfigLoader()._config = None

    # Execute
    response: QueryResponse = Orchestrator().run_query("q", cfg)
    tokens = response.metrics["execution_metrics"]["agent_tokens"]

    token_baseline(tokens)


def _simulate_multi_node() -> dict[str, float]:
    return simulate(node_count=4, duration=0.1)


def test_distributed_coordination_overhead(benchmark: BenchmarkFixture) -> None:
    """Benchmark coordination overhead across processes."""
    single = simulate(node_count=1, duration=0.1)
    multi = benchmark(_simulate_multi_node)

    assert multi["cpu_percent"] >= single["cpu_percent"]
