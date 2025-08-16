from autoresearch.agents.base import Agent, AgentRole
from autoresearch.agents.messages import MessageProtocol
from autoresearch.agents.registry import AgentFactory, AgentRegistry
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from autoresearch.orchestration.state import QueryState


class SimpleAgent(Agent):
    role: AgentRole = AgentRole.SPECIALIST

    def execute(self, state, config):
        return {}


def test_message_exchange_and_feedback():
    state = QueryState(query="q", coalitions={"team": ["Alice", "Bob"]})
    alice = SimpleAgent(name="Alice")
    bob = SimpleAgent(name="Bob")

    alice.send_message(state, "hello", to="Bob")
    bob_messages = bob.get_messages(state, from_agent="Alice")
    assert len(bob_messages) == 1
    assert bob_messages[0].content == "hello"

    bob.send_feedback(state, "Alice", "good job")
    feedback = alice.get_messages(state, from_agent="Bob")
    assert feedback[0].type == "feedback"
    assert feedback[0].content == "good job"
    assert len(state.feedback_events) == 1
    assert state.feedback_events[0].content == "good job"


def test_coalition_management_in_state():
    state = QueryState(query="q")
    state.add_coalition("c1", ["A", "B"])
    assert state.get_coalition_members("c1") == ["A", "B"]
    state.remove_coalition("c1")
    assert state.get_coalition_members("c1") == []


def test_agent_registry_coalitions():
    AgentFactory.register("Simple", SimpleAgent)
    AgentRegistry.create_coalition("squad", ["Simple"])
    assert "squad" in AgentRegistry.list_coalitions()
    assert AgentRegistry.get_coalition("squad") == ["Simple"]


def test_orchestrator_handles_coalitions(monkeypatch, tmp_path, orchestrator_runner):
    AgentFactory.register("A1", SimpleAgent)
    AgentFactory.register("A2", SimpleAgent)
    cfg = ConfigModel.model_construct(
        agents=["team"],
        loops=1,
        coalitions={"team": ["A1", "A2"]},
    )
    executed: list[str] = []

    def fake_get(name):
        agent = SimpleAgent(name=name)
        return agent

    def fake_execute_cycle(
        loop,
        loops,
        agents,
        primus_index,
        max_errors,
        state,
        config,
        metrics,
        callbacks,
        agent_factory,
        storage_manager,
        tracer,
        cb_manager,
    ):
        for agent in agents[primus_index]:
            executed.append(agent)
        return primus_index

    monkeypatch.setattr(AgentFactory, "get", staticmethod(fake_get))
    monkeypatch.setattr(OrchestrationUtils, "execute_cycle", fake_execute_cycle)
    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", str(tmp_path / "rel.json"))
    monkeypatch.setenv("AUTORESEARCH_QUERY_TOKENS", str(tmp_path / "qt.json"))

    orchestrator_runner().run_query("q", cfg)

    assert executed == ["A1", "A2"]


def test_message_protocols():
    state = QueryState(query="q", coalitions={"team": ["Alice", "Bob", "Charlie"]})
    state.messages = []
    alice = SimpleAgent(name="Alice")
    bob = SimpleAgent(name="Bob")
    charlie = SimpleAgent(name="Charlie")

    alice.send_message(state, "hello", to="Bob")
    assert state.messages[0]["protocol"] == MessageProtocol.DIRECT.value

    alice.broadcast(state, "hey team", "team")

    msgs_bob = bob.get_messages(
        state, from_agent="Alice", coalition="team", protocol=MessageProtocol.BROADCAST
    )
    msgs_charlie = charlie.get_messages(
        state, from_agent="Alice", coalition="team", protocol=MessageProtocol.BROADCAST
    )

    assert len(msgs_bob) >= 1 and len(msgs_charlie) >= 1
    assert msgs_bob[0].content == "hey team"
    assert msgs_bob[0].protocol == MessageProtocol.BROADCAST
