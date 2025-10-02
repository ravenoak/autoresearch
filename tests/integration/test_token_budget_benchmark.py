from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator, Protocol

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.orchestration.state import QueryState


pytestmark = pytest.mark.requires_llm


class TokenAdapterProtocol(Protocol):
    """Protocol for adapters that generate LLM responses."""

    def generate(self, prompt: str, model: str | None = None, **kwargs: object) -> str:
        ...


class DummyAgent:
    """Agent that emits a long prompt"""

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
        adapter: TokenAdapterProtocol | None = None,
    ) -> dict[str, dict[str, str]]:
        if adapter is None:  # pragma: no cover - defensive guard
            raise AssertionError("adapter must be provided")
        adapter.generate("one two three four five six")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_token_usage_budget_regression(
    monkeypatch: pytest.MonkeyPatch,
    token_baseline: Callable[[dict[str, dict[str, int]], int], None],
) -> None:
    """Token usage should respect the configured budget."""

    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: DummyAgent(name))

    captured_tokens: dict[str, dict[str, int]] = {}

    @contextmanager
    def no_capture(
        agent_name: str,
        metrics: OrchestrationMetrics,
        config: ConfigModel,
    ) -> Iterator[tuple[dict[str, int], TokenAdapterProtocol]]:
        token_counts: dict[str, int] = {"in": 0, "out": 0}

        class NullAdapter(TokenAdapterProtocol):
            def generate(
                self,
                prompt: str,
                model: str | None = None,
                **kwargs: object,
            ) -> str:
                token_counts["in"] += len(prompt.split())
                token_counts["out"] += 1
                return "ok"

        try:
            yield token_counts, NullAdapter()
        finally:
            captured_tokens[agent_name] = dict(token_counts)

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", no_capture)

    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy", token_budget=4)
    cfg.api.role_permissions["anonymous"] = ["query"]

    response: QueryResponse = Orchestrator().run_query("q", cfg)
    assert response.metrics["execution_metrics"].get("agent_tokens") is not None

    token_baseline(captured_tokens)
