from unittest.mock import patch
import asyncio

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


def test_custom_agents_order():
    record = []

    def get_agent(name):
        return DummyAgent(name, record)

    cfg = ConfigModel(agents=["A1", "A2", "A3"], loops=1)
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        side_effect=get_agent,
    ):
        Orchestrator.run_query("q", cfg)

    assert record == ["A1", "A2", "A3"]


def test_async_custom_agents_concurrent():
    record = []

    def get_agent(name):
        return DummyAgent(name, record)

    cfg = ConfigModel(agents=["A1", "A2", "A3"], loops=1)
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        side_effect=get_agent,
    ):
        asyncio.run(Orchestrator.run_query_async("q", cfg, concurrent=True))

    assert sorted(record) == ["A1", "A2", "A3"]
