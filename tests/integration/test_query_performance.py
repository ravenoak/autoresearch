# mypy: ignore-errors
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Protocol

import pytest

from autoresearch import resource_monitor
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.orchestration.state import QueryState

pytestmark = pytest.mark.slow


class TokenMetricsProtocol(Protocol):
    """Protocol describing the token metrics recorder used in tests."""

    def record_tokens(self, agent_name: str, in_tokens: int, out_tokens: int) -> None:
        ...


class PerfAgent:
    """Minimal agent for performance testing."""

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
        adapter: Callable[..., str] | None = None,
    ) -> dict[str, dict[str, str]]:
        if adapter is None:  # pragma: no cover - defensive guard
            raise AssertionError("adapter must be provided")
        adapter("dummy output")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def _build_perf_agent(
    name: str, llm_adapter: Callable[[str], object] | None = None
) -> PerfAgent:
    return PerfAgent(name)


def test_query_performance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure query performance stays within configured limits."""

    monkeypatch.setattr(AgentFactory, "get", _build_perf_agent)

    @contextmanager
    def capture(
        agent_name: str,
        metrics: TokenMetricsProtocol,
        config: ConfigModel,
    ) -> Iterator[tuple[dict[str, int], Callable[..., str]]]:
        token_counts = {"in": 0, "out": 0}

        class Adapter:
            def __call__(
                self,
                prompt: str,
                model: str | None = None,
                **kwargs: Any,
            ) -> str:
                token_counts["in"] += len(prompt.split())
                token_counts["out"] += 1
                return "ok"

            def generate(
                self,
                prompt: str,
                model: str | None = None,
                **kwargs: Any,
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
    response: QueryResponse = Orchestrator().run_query("performance test query", cfg)
    latency = time.perf_counter() - start
    _, mem_after = get_metrics()

    memory_delta = mem_after - mem_before
    tokens = response.metrics["execution_metrics"]["agent_tokens"]
    total_tokens = sum(v["in"] + v["out"] for v in tokens.values())

    assert latency <= cfg.user_preferences["max_latency_seconds"]
    assert memory_delta <= cfg.ram_budget_mb
    assert cfg.token_budget is None or total_tokens <= cfg.token_budget
