from pytest_bdd import scenario, given, when, then
from autoresearch.config import ConfigModel
from autoresearch.agents.base import Agent, AgentRole
from autoresearch.agents.registry import AgentFactory
from autoresearch.agents.messages import MessageProtocol
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState


class Sender(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Sender"

    def execute(self, state: QueryState, config: ConfigModel):
        self.send_message(state, "hi", to="Receiver")
        return {}


class Broadcaster(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Sender"

    def execute(self, state: QueryState, config: ConfigModel):
        self.broadcast(state, "hello team", "team")
        return {}


class Receiver(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Receiver"

    def execute(self, state: QueryState, config: ConfigModel):
        msgs = self.get_messages(state, from_agent="Sender")
        content = msgs[0].content if msgs else None
        state.results["received"] = content
        return {}


class TeamReceiver(Agent):
    role: AgentRole = AgentRole.SPECIALIST

    def execute(self, state: QueryState, config: ConfigModel):
        msgs = self.get_messages(
            state,
            from_agent="Sender",
            coalition="team",
            protocol=MessageProtocol.BROADCAST,
        )
        state.results[self.name] = msgs[0].content if msgs else None
        return {}


@scenario("../features/agent_messages.feature", "Agents share data through the orchestrator")
def test_agent_message_exchange():
    pass


@scenario("../features/agent_messages.feature", "Coalition broadcast communication")
def test_coalition_broadcast():
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


@given("a coalition with a sender and two receivers")
def setup_coalition(monkeypatch, bdd_context):
    cfg = ConfigModel(
        agents=["team"],
        loops=1,
        enable_agent_messages=True,
        coalitions={"team": ["Sender", "R1", "R2"]},
    )

    AgentFactory.register("Sender", Broadcaster)
    AgentFactory.register("R1", TeamReceiver)
    AgentFactory.register("R2", TeamReceiver)

    def get_agent(name):
        if name == "Sender":
            return Broadcaster()
        return TeamReceiver(name=name)

    monkeypatch.setattr(AgentFactory, "get", staticmethod(get_agent))
    bdd_context["config"] = cfg


@when("the sender broadcasts to the coalition")
def run_broadcast_query(bdd_context, monkeypatch):
    cfg = bdd_context["config"]
    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", "/tmp/release_tokens.json")
    monkeypatch.setenv("AUTORESEARCH_QUERY_TOKENS", "/tmp/query_tokens.json")
    bdd_context["response"] = Orchestrator.run_query("ping", cfg)


@then("both receivers should process the broadcast")
def receivers_got_broadcast(bdd_context):
    metrics = bdd_context["response"].metrics
    msgs_r1 = metrics["delivered_messages"]["R1"][0]
    msgs_r2 = metrics["delivered_messages"]["R2"][0]
    assert msgs_r1["protocol"] == "broadcast"
    assert msgs_r1["content"] == "hello team"
    assert msgs_r2["protocol"] == "broadcast"
    assert msgs_r2["content"] == "hello team"

