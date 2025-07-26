import pytest
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.config import ConfigModel


class DummyAgent:
    def can_execute(self, state, config):
        return True

    def execute(self, state, config, **_):
        return {"results": {"dummy": "ok"}}


class DummyFactory:
    @staticmethod
    def get(name: str):
        if name == "Dummy":
            return DummyAgent()
        raise ValueError("not found")


def test_get_agent_success():
    agent = Orchestrator._get_agent("Dummy", DummyFactory)
    assert isinstance(agent, DummyAgent)


def test_get_agent_not_found():
    with pytest.raises(Exception):
        Orchestrator._get_agent("Missing", DummyFactory)

    state = QueryState(query="q")
    cfg = ConfigModel.model_construct(enable_agent_messages=True)
    state.add_message({"to": "Dummy", "content": "hi"})
    Orchestrator._deliver_messages("Dummy", state, cfg)
    assert "Dummy" in state.metadata.get("delivered_messages", {})


def test_call_agent_start_callback():
    state = QueryState(query="q")
    calls = []
    Orchestrator._call_agent_start_callback(
        "Dummy", state, {"on_agent_start": lambda a, s: calls.append(a)}
    )
    assert calls == ["Dummy"]
