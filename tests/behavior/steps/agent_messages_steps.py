from pytest_bdd import given, when, then, scenario

from autoresearch.agents import Agent, MessageHandlerMixin
from pydantic import PrivateAttr
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.config import ConfigModel


class SenderAgent(Agent):
    name: str = "Sender"

    def execute(self, state, config):
        self.send_message(state, "ping", to="Receiver")
        return {}


class ReceiverAgent(Agent, MessageHandlerMixin):
    name: str = "Receiver"
    _received: list[str] = PrivateAttr(default_factory=list)

    def receive_messages(self, messages, state):
        for m in messages:
            self._received.append(m["content"])

    def execute(self, state, config):
        return {}


@given("agent messaging is enabled", target_fixture="agent_messaging_is_enabled")
def agent_messaging_is_enabled(monkeypatch, tmp_path):
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
    return {"config": cfg, "receiver": receiver}


@when("the orchestrator runs a messaging query", target_fixture="run_orchestrator")
def run_orchestrator(agent_messaging_is_enabled):
    Orchestrator.run_query("test", agent_messaging_is_enabled["config"])
    return agent_messaging_is_enabled


@then("the receiver agent should process the message")
def check_receiver(run_orchestrator):
    receiver = run_orchestrator["receiver"]
    assert receiver._received == ["ping"]


@scenario("../features/agent_messages.feature", "Messages are delivered between agents")
def test_agent_messages():
    pass
