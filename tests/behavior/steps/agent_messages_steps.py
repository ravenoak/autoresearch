from __future__ import annotations
from tests.behavior.utils import as_payload

from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, scenario, then, when

from autoresearch.agents.base import Agent, AgentRole
from autoresearch.agents.messages import MessageProtocol
from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState
from tests.behavior.context import (
    BehaviorContext,
    get_config,
    get_orchestrator,
    set_value,
)


class Sender(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Sender"

    def execute(self, state: QueryState, config: ConfigModel) -> dict[str, Any]:
        self.send_message(state, "hi", to="Receiver")
        return as_payload({})


class Broadcaster(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Sender"

    def execute(self, state: QueryState, config: ConfigModel) -> dict[str, Any]:
        self.broadcast(state, "hello team", "team")
        return as_payload({})


class Receiver(Agent):
    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Receiver"

    def execute(self, state: QueryState, config: ConfigModel) -> dict[str, Any]:
        msgs = self.get_messages(state, from_agent="Sender")
        content = msgs[0].content if msgs else None
        state.results["received"] = content
        return as_payload({})


class TeamReceiver(Agent):
    role: AgentRole = AgentRole.SPECIALIST

    def execute(self, state: QueryState, config: ConfigModel) -> dict[str, Any]:
        msgs = self.get_messages(
            state,
            from_agent="Sender",
            coalition="team",
            protocol=MessageProtocol.BROADCAST,
        )
        state.results[self.name] = msgs[0].content if msgs else None
        return as_payload({})


@scenario(
    "../features/agent_messages.feature", "Agents share data through the orchestrator"
)
def test_agent_message_exchange() -> None:
    pass


@scenario("../features/agent_messages.feature", "Coalition broadcast communication")
def test_coalition_broadcast() -> None:
    pass


@scenario(
    "../features/agent_messages.feature", "Messaging disabled prevents communication"
)
def test_messaging_disabled() -> None:
    pass


@given("two communicating agents", target_fixture="config")
def setup_agents(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    config_model: ConfigModel,
    bdd_context: BehaviorContext,
) -> ConfigModel:
    """Configure a simple pair of communicating agents."""
    db_path = tmp_path / "kg.duckdb"
    cfg = config_model.model_copy()
    cfg.agents = ["Sender", "Receiver"]
    cfg.loops = 1
    cfg.enable_agent_messages = True
    cfg.storage = StorageConfig(duckdb_path=str(db_path))
    monkeypatch.setenv("DUCKDB_PATH", str(db_path))

    def get_agent(name: str) -> Agent:
        return Sender() if name == "Sender" else Receiver()

    monkeypatch.setattr(AgentFactory, "get", staticmethod(get_agent))
    set_value(bdd_context, "config", cfg)
    return cfg


@given("two communicating agents without messaging", target_fixture="config")
def setup_agents_no_messaging(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    config_model: ConfigModel,
    bdd_context: BehaviorContext,
) -> ConfigModel:
    """Configure agents with messaging disabled."""
    db_path = tmp_path / "kg.duckdb"
    cfg = config_model.model_copy()
    cfg.agents = ["Sender", "Receiver"]
    cfg.loops = 1
    cfg.enable_agent_messages = False
    cfg.storage = StorageConfig(duckdb_path=str(db_path))
    monkeypatch.setenv("DUCKDB_PATH", str(db_path))

    def get_agent(name: str) -> Agent:
        return Sender() if name == "Sender" else Receiver()

    monkeypatch.setattr(AgentFactory, "get", staticmethod(get_agent))
    set_value(bdd_context, "config", cfg)
    return cfg


@when("I execute a query", target_fixture="response")
def run_query(bdd_context: BehaviorContext) -> QueryResponse:
    """Execute a simple query and capture the response."""
    orchestrator = get_orchestrator(bdd_context)
    config = get_config(bdd_context)
    return orchestrator.run_query("ping", config)


@then("the receiver should process the message")
def receiver_got_message(response: QueryResponse) -> None:
    metrics = response.metrics
    assert metrics["delivered_messages"]["Receiver"][0]["content"] == "hi"


@then("the receiver should have no messages")
def receiver_no_message(response: QueryResponse) -> None:
    metrics = response.metrics
    assert "Receiver" not in metrics.get("delivered_messages", {})


@given("a coalition with a sender and two receivers", target_fixture="config")
def setup_coalition(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    config_model: ConfigModel,
    bdd_context: BehaviorContext,
) -> ConfigModel:
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

    def get_agent(name: str) -> Agent:
        if name == "Sender":
            return Broadcaster()
        return TeamReceiver(name=name)

    monkeypatch.setattr(AgentFactory, "get", staticmethod(get_agent))
    set_value(bdd_context, "config", cfg)
    return cfg


@when("the sender broadcasts to the coalition", target_fixture="response")
def run_broadcast_query(bdd_context: BehaviorContext) -> QueryResponse:
    """Run a query to trigger broadcast messaging."""
    orchestrator = get_orchestrator(bdd_context)
    config = get_config(bdd_context)
    return orchestrator.run_query("ping", config)


@then("both receivers should process the broadcast")
def receivers_got_broadcast(response: QueryResponse) -> None:
    metrics = response.metrics
    msgs_r1 = metrics["delivered_messages"]["R1"][0]
    msgs_r2 = metrics["delivered_messages"]["R2"][0]
    assert msgs_r1["protocol"] == "broadcast"
    assert msgs_r1["content"] == "hello team"
    assert msgs_r2["protocol"] == "broadcast"
    assert msgs_r2["content"] == "hello team"
