import pytest
from unittest.mock import patch

from autoresearch.agents import Agent, MessageHandlerMixin
from pydantic import PrivateAttr
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.config import ConfigModel


class SenderAgent(Agent):
    name: str = "Sender"

    def execute(self, state, config):
        self.send_message(state, "hi", to="Receiver")
        return {"results": {"sent": True}}


class ReceiverAgent(Agent, MessageHandlerMixin):
    name: str = "Receiver"

    _received: list[str] = PrivateAttr(default_factory=list)

    def receive_messages(self, messages, state):
        for m in messages:
            self._received.append(m["content"])

    def execute(self, state, config):
        return {"results": {"received": self._received}}


def test_orchestrator_routes_messages(monkeypatch, tmp_path):
    cfg = ConfigModel(
        agents=["Sender", "Receiver"],
        loops=1,
        enable_agent_messages=True,
    )

    sender = SenderAgent()
    receiver = ReceiverAgent()

    def get_agent(name):
        return sender if name == "Sender" else receiver

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get", get_agent
    )

    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", str(tmp_path / "rel.json"))
    monkeypatch.setenv("AUTORESEARCH_QUERY_TOKENS", str(tmp_path / "query.json"))

    Orchestrator.run_query("q", cfg)

    assert receiver._received == ["hi"]
