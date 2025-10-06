# mypy: ignore-errors
from __future__ import annotations

from typing import cast

import pytest
from unittest.mock import MagicMock

from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.errors import NotFoundError, StorageError
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from autoresearch.orchestration.state import QueryState
from tests.typing_helpers import AgentFactoryProtocol, AgentTestProtocol


class DummyAgent:
    """Simple agent used to validate OrchestrationUtils helpers."""

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        return True

    def execute(
        self, state: QueryState, config: ConfigModel, **_: object
    ) -> dict[str, object]:
        return {"results": {"dummy": "ok"}}


class DummyFactory(AgentFactoryProtocol):
    """Factory that resolves the dummy agent by name."""

    @staticmethod
    def get(name: str) -> AgentTestProtocol:
        if name == "Dummy":
            return DummyAgent()
        raise ValueError("not found")


def test_get_agent_success() -> None:
    factory = cast(type[AgentFactory], DummyFactory)
    agent = OrchestrationUtils.get_agent("Dummy", factory)
    assert isinstance(agent, DummyAgent)


def test_get_agent_not_found() -> None:
    factory = cast(type[AgentFactory], DummyFactory)
    with pytest.raises(NotFoundError) as excinfo:
        OrchestrationUtils.get_agent("Missing", factory)
    assert isinstance(excinfo.value.__cause__, ValueError)

    state = QueryState(query="q")
    cfg = ConfigModel(enable_agent_messages=True)
    state.add_message({"to": "Dummy", "content": "hi"})
    OrchestrationUtils.deliver_messages("Dummy", state, cfg)
    assert "Dummy" in state.metadata.get("delivered_messages", {})


def test_call_agent_start_callback() -> None:
    state = QueryState(query="q")
    calls: list[str] = []

    def _capture(agent_name: str, _: QueryState) -> None:
        calls.append(agent_name)

    callbacks = {"on_agent_start": _capture}
    OrchestrationUtils.call_agent_start_callback("Dummy", state, callbacks)
    assert calls == ["Dummy"]


def test_persist_claims_logs_storage_error(caplog: pytest.LogCaptureFixture) -> None:
    storage = MagicMock()
    storage.persist_claim.side_effect = StorageError("fail")
    result: dict[str, object] = {"claims": [{"id": "c1"}]}

    with caplog.at_level("WARNING"):
        OrchestrationUtils.persist_claims("Agent", result, storage)

    assert "Error persisting claims for agent Agent" in caplog.text
