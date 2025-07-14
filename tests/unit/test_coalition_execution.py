from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.config import ConfigModel

class DummyAgent:
    def __init__(self, name, record):
        self.name = name
        self.record = record

    def can_execute(self, state, config):
        return True

    def execute(self, state, config):
        self.record.append(self.name)
        return {}


def test_coalition_agents_run_together(monkeypatch):
    record = []

    def get_agent(name):
        return DummyAgent(name, record)

    cfg = ConfigModel(agents=["team"], loops=1, coalitions={"team": ["A", "B"]})

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get", get_agent
    )

    Orchestrator.run_query("q", cfg)

    assert record == ["A", "B"]
