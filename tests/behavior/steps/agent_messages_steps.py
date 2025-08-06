from pytest_bdd import scenario, given, when, then
from . import common_steps  # noqa: F401
from autoresearch.config.models import ConfigModel, StorageConfig
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


@given("two communicating agents", target_fixture="config")
def setup_agents(monkeypatch, tmp_path, config_model):
    """Configure a simple pair of communicating agents."""
    db_path = tmp_path / "kg.duckdb"
    cfg = config_model.model_copy()
    cfg.agents = ["Sender", "Receiver"]
    cfg.loops = 1
    cfg.enable_agent_messages = True
    cfg.storage = StorageConfig(duckdb_path=str(db_path))
    monkeypatch.setenv("DUCKDB_PATH", str(db_path))

    def get_agent(name: str):
        return Sender() if name == "Sender" else Receiver()

    monkeypatch.setattr(AgentFactory, "get", staticmethod(get_agent))
    return cfg


@when("I execute a query", target_fixture="response")
def run_query(config):
    """Execute a simple query and capture the response."""
    return Orchestrator.run_query("ping", config)


@then("the receiver should process the message")
def receiver_got_message(response):
    metrics = response.metrics
    assert metrics["delivered_messages"]["Receiver"][0]["content"] == "hi"


@given("a coalition with a sender and two receivers", target_fixture="config")
def setup_coalition(monkeypatch, tmp_path, config_model):
    """Set up a coalition for broadcast testing."""
    db_path = tmp_path / "kg.duckdb"
    cfg = config_model.model_copy()
    cfg.agents = ["team"]
    cfg.loops = 1
    cfg.enable_agent_messages = True
    cfg.coalitions = {"team": ["Sender", "R1", "R2"]}
    cfg.storage = StorageConfig(duckdb_path=str(db_path))
    monkeypatch.setenv("DUCKDB_PATH", str(db_path))

    AgentFactory.register("Sender", Broadcaster)
    AgentFactory.register("R1", TeamReceiver)
    AgentFactory.register("R2", TeamReceiver)

    def get_agent(name: str):
        if name == "Sender":
            return Broadcaster()
        return TeamReceiver(name=name)

    monkeypatch.setattr(AgentFactory, "get", staticmethod(get_agent))
    return cfg


@when("the sender broadcasts to the coalition", target_fixture="response")
def run_broadcast_query(config):
    """Run a query to trigger broadcast messaging."""
    return Orchestrator.run_query("ping", config)


@then("both receivers should process the broadcast")
def receivers_got_broadcast(response):
    metrics = response.metrics
    msgs_r1 = metrics["delivered_messages"]["R1"][0]
    msgs_r2 = metrics["delivered_messages"]["R2"][0]
    assert msgs_r1["protocol"] == "broadcast"
    assert msgs_r1["content"] == "hello team"
    assert msgs_r2["protocol"] == "broadcast"
    assert msgs_r2["content"] == "hello team"
