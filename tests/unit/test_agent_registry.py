import pytest

from autoresearch.agents.registry import AgentFactory, AgentRegistry


class DummyAgent:
    def __init__(self, name: str):
        self.name = name

    def can_execute(self, state, config):
        return True

    def execute(self, state, config):
        return {}


def test_register_and_get_cached_instance():
    AgentFactory.register("Dummy", DummyAgent)
    agent1 = AgentFactory.get("Dummy")
    agent2 = AgentFactory.get("Dummy")
    assert isinstance(agent1, DummyAgent)
    assert agent1 is agent2
    assert "Dummy" in AgentRegistry.list_available()


def test_get_unknown_agent_raises():
    with pytest.raises(ValueError):
        AgentFactory.get("Missing")


def test_reset_instances(monkeypatch):
    AgentFactory.register("Dummy", DummyAgent)
    agent1 = AgentFactory.get("Dummy")
    AgentFactory.reset_instances()
    agent2 = AgentFactory.get("Dummy")
    assert agent1 is not agent2
