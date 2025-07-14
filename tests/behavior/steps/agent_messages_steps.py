from pytest_bdd import scenario, given, when, then
from autoresearch.config import ConfigModel
from pytest_bdd import scenario, given, when, then
from autoresearch.agents.base import Agent, AgentRole
from autoresearch.agents.registry import AgentFactory
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState


class Sender(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Sender"

    def execute(self, state: QueryState, config: ConfigModel):
        self.send_message(state, "hi", to="Receiver")
        return {}


class Receiver(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Receiver"

    def execute(self, state: QueryState, config: ConfigModel):
        msgs = self.get_messages(state, from_agent="Sender")
        content = msgs[0].content if msgs else None
        state.results["received"] = content
        return {}


@scenario("../features/agent_messages.feature", "Agents share data through the orchestrator")
def test_agent_message_exchange():
    pass


@given("two communicating agents")
def setup_agents(monkeypatch, bdd_context):
    cfg = ConfigModel(agents=["Sender", "Receiver"], loops=1, enable_agent_messages=True)

    def get_agent(name):
        return Sender() if name == "Sender" else Receiver()

    monkeypatch.setattr(AgentFactory, "get", staticmethod(get_agent))
    bdd_context["config"] = cfg


@when("I execute a query")
def run_query(bdd_context, monkeypatch):
    cfg = bdd_context["config"]
    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", "/tmp/release_tokens.json")
    monkeypatch.setenv("AUTORESEARCH_QUERY_TOKENS", "/tmp/query_tokens.json")
    bdd_context["response"] = Orchestrator.run_query("ping", cfg)


@then("the receiver should process the message")
def receiver_got_message(bdd_context):
    metrics = bdd_context["response"].metrics
    assert metrics["delivered_messages"]["Receiver"][0]["content"] == "hi"
