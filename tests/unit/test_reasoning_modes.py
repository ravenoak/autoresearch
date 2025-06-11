from unittest.mock import patch

from autoresearch.config import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration import ReasoningMode


class DummyAgent:
    def __init__(self, name, record):
        self.name = name
        self.record = record

    def can_execute(self, state, config):
        return True

    def execute(self, state, config):
        self.record.append(self.name)
        return {}


def _run(cfg):
    record = []

    def get_agent(name):
        return DummyAgent(name, record)

    with patch("autoresearch.orchestration.orchestrator.AgentFactory.get", side_effect=get_agent):
        Orchestrator.run_query("q", cfg)

    return record


def test_direct_mode_executes_once():
    cfg = ConfigModel(loops=3, reasoning_mode=ReasoningMode.DIRECT)
    record = _run(cfg)
    assert record == ["Synthesizer"]


def test_chain_of_thought_mode_loops():
    cfg = ConfigModel(loops=2, reasoning_mode=ReasoningMode.CHAIN_OF_THOUGHT)
    record = _run(cfg)
    assert record == ["Synthesizer", "Synthesizer"]
