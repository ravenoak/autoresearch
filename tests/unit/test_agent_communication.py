from autoresearch.agents.base import Agent, AgentRole
from autoresearch.agents.registry import AgentFactory, AgentRegistry
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
