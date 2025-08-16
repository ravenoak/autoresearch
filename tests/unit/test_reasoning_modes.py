from unittest.mock import patch

from autoresearch.config.models import ConfigModel
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


def _run(cfg, orchestrator_runner):
    record = []

    def get_agent(name):
        return DummyAgent(name, record)

    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        side_effect=get_agent,
    ):
        orchestrator_runner().run_query("q", cfg)

    return record


def test_direct_mode_executes_once(orchestrator_runner):
    cfg = ConfigModel(loops=3, reasoning_mode=ReasoningMode.DIRECT)
    record = _run(cfg, orchestrator_runner)
    assert record == ["Synthesizer"]


def test_chain_of_thought_mode_loops(orchestrator_runner):
    cfg = ConfigModel(loops=2, reasoning_mode=ReasoningMode.CHAIN_OF_THOUGHT)
    record = _run(cfg, orchestrator_runner)
    assert record == ["Synthesizer", "Synthesizer"]


def test_chain_of_thought_records_steps(orchestrator_runner):
    cfg = ConfigModel(loops=3, reasoning_mode=ReasoningMode.CHAIN_OF_THOUGHT)

    class DummySynth:
        def __init__(self):
            self.idx = 0

        def can_execute(self, state, config):
            return True

        def execute(self, state, config):
            self.idx += 1
            content = f"step-{self.idx}"
            return {
                "claims": [
                    {
                        "id": str(self.idx),
                        "type": "thought",
                        "content": content,
                    }
                ],
                "results": {"final_answer": content},
            }

    agent = DummySynth()
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        return_value=agent,
    ):
        resp = orchestrator_runner().run_query("q", cfg)

    steps = [c["content"] for c in resp.reasoning]
    assert steps == ["step-1", "step-2", "step-3"]
    assert resp.answer == "step-3"
