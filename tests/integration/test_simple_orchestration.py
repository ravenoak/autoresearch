from typing import Any

import pytest

from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.models import QueryResponse
from autoresearch.storage import StorageManager


def make_agent(name: str, calls: list[str]):

    class DummyAgent:
        def __init__(self, agent_name: str, llm_adapter: Any | None = None) -> None:
            self.name = agent_name

        def can_execute(self, state: Any, config: ConfigModel) -> bool:
            return True

        def execute(self, state: Any, config: ConfigModel, **kwargs: Any) -> dict[str, Any]:
            calls.append(self.name)
            state.update(
                {
                    "results": {self.name: "ok"},
                    "claims": [
                        {"type": "fact", "content": self.name, "id": self.name}
                    ],
                }
            )
            if self.name == "Synthesizer":
                state.results["final_answer"] = f"Answer from {self.name}"
            return {
                "results": {self.name: "ok"},
                "claims": [
                    {"type": "fact", "content": self.name, "id": self.name}
                ],
            }

    return DummyAgent(name)


def test_orchestrator_run_query(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: None)
    monkeypatch.setattr(AgentFactory, "get", lambda name: make_agent(name, calls))

    cfg = ConfigModel(agents=["Synthesizer"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    response = Orchestrator().run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert calls == ["Synthesizer"]
    assert response.answer == "Answer from Synthesizer"
