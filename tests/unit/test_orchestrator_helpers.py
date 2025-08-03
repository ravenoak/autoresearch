import pytest
from unittest.mock import MagicMock

from autoresearch.config.models import ConfigModel
from autoresearch.errors import NotFoundError, StorageError
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState


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
    with pytest.raises(NotFoundError) as excinfo:
        Orchestrator._get_agent("Missing", DummyFactory)
    assert isinstance(excinfo.value.__cause__, ValueError)

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


def test_persist_claims_logs_storage_error(caplog):
    storage = MagicMock()
    storage.persist_claim.side_effect = StorageError("fail")
    result = {"claims": [{"id": "c1"}]}

    with caplog.at_level("WARNING"):
        Orchestrator._persist_claims("Agent", result, storage)

    assert "Error persisting claims for agent Agent" in caplog.text
