# mypy: ignore-errors
"""Integration test for token usage tracking against baselines."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Protocol

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.orchestration.state import QueryState

# Allow tokens to exceed the baseline by this many tokens before failing
THRESHOLD = int(os.getenv("TOKEN_USAGE_THRESHOLD", "0"))

pytestmark = [pytest.mark.slow, pytest.mark.requires_llm]

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_usage.json"


class TokenAdapterProtocol(Protocol):
    """Protocol for adapters that generate responses."""

    def generate(self, prompt: str, model: str | None = None, **kwargs: object) -> str:
        ...


class DummyAgent:
    """Simple agent that generates a single prompt."""

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
        adapter.generate("hello world")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_token_usage_matches_baseline(
    monkeypatch: pytest.MonkeyPatch,
    token_baseline: Callable[[dict[str, dict[str, int]], int], None],
) -> None:
    """Token counts should match the stored baseline."""

    # Setup a minimal configuration and agent
    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: DummyAgent(name))
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy")
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    response: QueryResponse = Orchestrator().run_query("q", cfg)
    tokens: dict[str, dict[str, int]] = response.metrics["execution_metrics"]["agent_tokens"]

    baseline: dict[str, dict[str, int]] = json.loads(BASELINE_PATH.read_text())
    for agent, counts in baseline.items():
        for direction in ("in", "out"):
            measured = tokens.get(agent, {}).get(direction, 0)
            expected = counts.get(direction, 0)
            assert abs(measured - expected) <= THRESHOLD

    token_baseline(tokens, THRESHOLD)
