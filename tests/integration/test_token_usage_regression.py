# mypy: ignore-errors
"""Regression test ensuring token usage stays within baseline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Protocol

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.orchestration.state import QueryState

pytestmark = [pytest.mark.slow, pytest.mark.requires_llm]

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_usage.json"
THRESHOLD = 0.10  # allow up to 10% more tokens than baseline


class TokenAdapterProtocol(Protocol):
    """Protocol for adapters used during token accounting."""

    def generate(self, prompt: str, model: str | None = None, **kwargs: object) -> str:
        ...


class DummyAgent:
    """Simple agent used for token counting."""

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
    ) -> dict[str, dict[str, str]]:  # pragma: no cover - minimal logic
        if adapter is None:
            raise AssertionError("adapter must be provided")
        adapter.generate("hello world")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def test_token_usage_regression(monkeypatch: pytest.MonkeyPatch) -> None:
    """Token usage should not grow beyond 10% of the baseline."""

    # Configure orchestrator with a single dummy agent
    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: DummyAgent(name))
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy")
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    response: QueryResponse = Orchestrator().run_query("q", cfg)
    tokens: dict[str, dict[str, int]] = response.metrics["execution_metrics"]["agent_tokens"]
    total_tokens = sum(v.get("in", 0) + v.get("out", 0) for v in tokens.values())

    baseline_total = 0
    if BASELINE_PATH.exists():
        baseline: dict[str, dict[str, int]] = json.loads(BASELINE_PATH.read_text())
        baseline_total = sum(v.get("in", 0) + v.get("out", 0) for v in baseline.values())
        allowed = baseline_total * (1 + THRESHOLD)
        assert (
            total_tokens <= allowed
        ), f"Total tokens {total_tokens} exceed baseline {baseline_total} by more than 10%"

    BASELINE_PATH.write_text(json.dumps(tokens, indent=2, sort_keys=True))
