# mypy: ignore-errors
from collections.abc import Callable
from typing import Any

import pytest

from autoresearch.test_tools import MCPTestClient
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse
from tests.typing_helpers import TypedFixture


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def json(self):
        return self._json


pytestmark = pytest.mark.slow


@pytest.fixture()
def mcp_setup(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[ConfigModel]:
    config = ConfigModel(agents=["Synthesizer", "Contrarian", "FactChecker"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)

    def dummy_run_query(
        query: str,
        cfg: ConfigModel,
        callbacks: Callable[..., object] | None = None,
        **kwargs: Any,
    ) -> QueryResponse:
        if query == "fail":
            raise RuntimeError("boom")
        if cfg.reasoning_mode == ReasoningMode.DIRECT:
            order = ["Synthesizer"]
        elif cfg.reasoning_mode == ReasoningMode.CHAIN_OF_THOUGHT:
            order = ["Synthesizer"] * cfg.loops
        else:
            order = []
            for _ in range(cfg.loops):
                order.extend(cfg.agents)
        reasoning = [{"content": name} for name in order]
        return QueryResponse(answer=order[-1], citations=[], reasoning=reasoning, metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)

    def mock_post(
        url: str,
        json: dict[str, Any] | None = None,
        **_kwargs: Any,
    ) -> DummyResponse:
        try:
            payload = dict(json or {})
            resp = dummy_run_query(payload["query"], config)
            data = {
                "answer": resp.answer,
                "citations": resp.citations,
                "reasoning": resp.reasoning,
                "metrics": resp.metrics,
            }
        except Exception as exc:  # pragma: no cover - error path
            data = {"error": str(exc)}
        return DummyResponse(status_code=200, json_data=data)

    monkeypatch.setattr("requests.post", mock_post)
    monkeypatch.setattr("requests.get", lambda *_a, **_k: DummyResponse(status_code=200, text="ok"))

    return config


def test_dialectical_mode_agents(monkeypatch, mcp_setup):
    config = mcp_setup
    config.reasoning_mode = ReasoningMode.DIALECTICAL
    client = MCPTestClient()
    result = client.test_research_tool("query")
    assert result["status"] == "success"
    names = [step["content"] for step in result["response"]["reasoning"]]
    assert names == ["Synthesizer", "Contrarian", "FactChecker"]


def test_direct_and_cot_modes(monkeypatch, mcp_setup):
    config = mcp_setup
    client = MCPTestClient()

    config.reasoning_mode = ReasoningMode.DIRECT
    direct = client.test_research_tool("q")
    assert [s["content"] for s in direct["response"]["reasoning"]] == ["Synthesizer"]

    config.reasoning_mode = ReasoningMode.CHAIN_OF_THOUGHT
    config.loops = 2
    cot = client.test_research_tool("q")
    assert [s["content"] for s in cot["response"]["reasoning"]] == ["Synthesizer", "Synthesizer"]


def test_failure_recovery(monkeypatch, mcp_setup):
    config = mcp_setup
    config.reasoning_mode = ReasoningMode.DIALECTICAL
    client = MCPTestClient()
    results = client.run_test_suite(["ok", "fail"])

    assert results["connection_test"]["status"] == "success"
    assert results["research_tests"][0]["result"]["status"] == "success"
    assert "error" in results["research_tests"][1]["result"]
