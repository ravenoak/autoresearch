from autoresearch.agents.base import Agent, AgentRole
from autoresearch.config.models import ConfigModel
from autoresearch.agents.registry import AgentFactory
from autoresearch.orchestration.state import QueryState


class Sender(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Sender"

    def execute(self, state: QueryState, config: ConfigModel):
        self.send_message(state, "ping", to="Receiver")
        return {"results": {"sent": True}}


class Receiver(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Receiver"

    def execute(self, state: QueryState, config: ConfigModel):
        msgs = self.get_messages(state, from_agent="Sender")
        content = msgs[0].content if msgs else None
        return {"results": {"received": content}}


def test_agents_exchange_messages(monkeypatch, orchestrator_runner):
    cfg = ConfigModel(agents=["Sender", "Receiver"], loops=1, enable_agent_messages=True)

    def get_agent(name):
        return Sender() if name == "Sender" else Receiver()

    monkeypatch.setattr(AgentFactory, "get", staticmethod(get_agent))

    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", "/tmp/release_tokens.json")
    monkeypatch.setenv("AUTORESEARCH_QUERY_TOKENS", "/tmp/query_tokens.json")
    resp = orchestrator_runner().run_query("test", cfg)

    assert resp.answer == "No answer synthesized"
    assert resp.metrics["delivered_messages"]["Receiver"][0]["content"] == "ping"
