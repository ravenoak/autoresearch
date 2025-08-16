
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.config.models import ConfigModel
from autoresearch.agents.registry import AgentFactory


class DummyAgent:
    def __init__(self, name, record):
        self.name = name
        self.record = record

    def can_execute(self, state, config):
        return True

    def execute(self, state, config):
        self.record.append(self.name)
        return {}


def test_coalition_agents_run_together(monkeypatch, tmp_path, orchestrator_runner):
    record = []
    AgentFactory._registry.clear()

    def get_agent(name):
        return DummyAgent(name, record)

    AgentFactory.register("A", DummyAgent)
    AgentFactory.register("B", DummyAgent)

    cfg = ConfigModel.from_dict(
        {"loops": 1, "agents": ["team"], "coalitions": {"team": ["A", "B"]}}
    )

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get", get_agent
    )
    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", str(tmp_path / "rel.json"))
    monkeypatch.setenv("AUTORESEARCH_QUERY_TOKENS", str(tmp_path / "qt.json"))

    orchestrator_runner().run_query("q", cfg)

    assert set(record[:2]) == {"A", "B"}


def test_configmodel_from_dict_allows_coalitions():
    cfg = ConfigModel.from_dict(
        {"loops": 1, "agents": ["team"], "coalitions": {"team": ["A", "B"]}}
    )
    assert cfg.agents == ["team"]
    assert cfg.coalitions == {"team": ["A", "B"]}
