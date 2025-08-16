import asyncio
from unittest.mock import patch

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import Orchestrator


class DummyAgent:
    def __init__(self, name, record):
        self.name = name
        self.record = record

    def can_execute(self, state, config):
        return True

    def execute(self, state, config):
        self.record.append(self.name)
        return {}


def test_custom_agents_order(orchestrator):
    record = []

    def get_agent(name):
        return DummyAgent(name, record)

    cfg = ConfigModel(agents=["A1", "A2", "A3"], loops=1)
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        side_effect=get_agent,
    ):
        orchestrator.run_query("q", cfg)

    assert record == ["A1", "A2", "A3"]


def test_async_custom_agents_concurrent(orchestrator):
    record = []

    def get_agent(name):
        return DummyAgent(name, record)

    cfg = ConfigModel(agents=["A1", "A2", "A3"], loops=1)
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        side_effect=get_agent,
    ):
        orch = orchestrator
        asyncio.run(orch.run_query_async("q", cfg, concurrent=True))

    assert sorted(record) == ["A1", "A2", "A3"]


def test_parse_config_direct_mode_groups():
    cfg = ConfigModel(reasoning_mode=ReasoningMode.DIRECT, loops=5)
    params = Orchestrator._parse_config(cfg)
    assert params["agent_groups"] == [["Synthesizer"]]
    assert params["loops"] == 1
