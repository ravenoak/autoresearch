from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.config import ConfigModel, ConfigLoader
from autoresearch.models import QueryResponse
from autoresearch.storage import StorageManager


def make_agent(name, calls):

    class DummyAgent:
        def __init__(self, name, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):
            return True

        def execute(self, state, config, **kwargs):
            calls.append(self.name)
            state.update({
                "results": {self.name: "ok"},
                "claims": [{"type": "fact", "content": self.name, "id": self.name}]
            })
            if self.name == "Synthesizer":
                state.results["final_answer"] = f"Answer from {self.name}"
            return {
                "results": {self.name: "ok"},
                "claims": [{"type": "fact", "content": self.name, "id": self.name}],
            }
    return DummyAgent(name)


def test_orchestrator_run_query(monkeypatch):
    calls = []
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: None)
    monkeypatch.setattr(AgentFactory, "get", lambda name: make_agent(name, calls))

    cfg = ConfigModel(agents=["Synthesizer"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    response = Orchestrator.run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert calls == ["Synthesizer"]
    assert response.answer == "Answer from Synthesizer"
