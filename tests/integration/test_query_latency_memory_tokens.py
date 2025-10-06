# mypy: ignore-errors
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Protocol

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageManager

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TokenMetricsProtocol(Protocol):
    """Protocol capturing the metrics recorder interface used by the tests."""

    def record_tokens(self, agent_name: str, in_tokens: int, out_tokens: int) -> None:
        ...


class BenchAgent:
    def __init__(
        self,
        name: str,
        llm_adapter: Callable[[str], object] | None = None,
    ) -> None:
        self.name = name

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        return True

    def execute(
        self,
        state: QueryState,
        config: ConfigModel,
        adapter: Callable[[str], str] | None = None,
    ) -> dict[str, dict[str, str]]:
        if adapter is None:  # pragma: no cover - defensive guard
            raise AssertionError("adapter must be provided")
        adapter("benchmark prompt")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def _build_bench_agent(
    name: str, llm_adapter: Callable[[str], object] | None = None
) -> BenchAgent:
    return BenchAgent(name)


def test_query_latency_memory_tokens(
    monkeypatch: pytest.MonkeyPatch,
    token_baseline: Callable[[dict[str, dict[str, int]], int], None],
) -> None:
    monkeypatch.setattr(AgentFactory, "get", _build_bench_agent)

    @contextmanager
    def capture(
        agent_name: str,
        metrics: TokenMetricsProtocol,
        config: ConfigModel,
    ) -> Iterator[tuple[dict[str, Any], Callable[[str], str]]]:
        def generate(prompt: str) -> str:
            metrics.record_tokens(agent_name, len(prompt.split()), 1)
            return "ok"

        yield ({}, generate)

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", capture)

    cfg = ConfigModel(agents=["BenchAgent"], loops=1, llm_backend="dummy")
    cfg.api.role_permissions["anonymous"] = ["query"]

    memory_before = StorageManager._current_ram_mb()
    start = time.perf_counter()
    response: QueryResponse = Orchestrator().run_query("q", cfg)
    latency = time.perf_counter() - start
    memory_after = StorageManager._current_ram_mb()

    tokens = response.metrics["execution_metrics"]["agent_tokens"]
    token_baseline(tokens)

    assert latency < 1.0
    assert memory_after - memory_before < 50
