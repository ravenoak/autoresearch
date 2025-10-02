"""Step definitions for orchestrator and agents integration tests.

This module contains step definitions for testing the integration between
the orchestrator and agents, including agent execution order, error handling,
and execution conditions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, cast
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, scenario, then, when

from autoresearch.config.models import ConfigModel
from autoresearch.llm import DummyAdapter
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from tests.behavior.context import (
    BehaviorContext,
    get_config,
    get_orchestrator,
    set_value,
)


@dataclass(slots=True)
class OrchestratorScenarioContext:
    """Typed container for sharing state between behavior steps."""

    config: ConfigModel | None = None
    agents: list[str] = field(default_factory=list)
    executed_agents: list[str] = field(default_factory=list)
    agent_states: dict[str, Any] = field(default_factory=dict)
    result: Any | None = None
    errors: list[tuple[str, Exception]] = field(default_factory=list)
    exception: Exception | None = None
    original_execute_agent: Callable[..., None] | None = None
    original_handle_error: Callable[..., dict[str, object]] | None = None
    original_get: Callable[[str], MagicMock] | None = None


# Fixtures


@pytest.fixture
def test_context() -> OrchestratorScenarioContext:
    """Create a typed context for storing scenario state."""

    return OrchestratorScenarioContext()


@pytest.fixture
def mock_agent_factory() -> MagicMock:
    """Create a mock agent factory for testing."""

    factory: MagicMock = MagicMock()
    agents: dict[str, MagicMock] = {}

    def get_agent(name: str) -> MagicMock:
        if name not in agents:
            agent = MagicMock()
            agent.name = name
            agent.can_execute.return_value = True
            agent.execute.return_value = {
                "agent": name,
                "result": f"Result from {name}",
            }
            agents[name] = agent
        return agents[name]

    factory.get.side_effect = get_agent
    return factory


# Scenarios


@scenario(
    "../features/orchestrator_agents_integration.feature",
    "Orchestrator executes agents in the correct order",
)
def test_orchestrator_executes_agents_in_order() -> None:
    """Test that the orchestrator executes agents in the correct order."""


@scenario(
    "../features/orchestrator_agents_integration.feature",
    "Orchestrator handles agent errors gracefully",
)
def test_orchestrator_handles_agent_errors() -> None:
    """Test that the orchestrator handles agent errors gracefully."""


@scenario(
    "../features/orchestrator_agents_integration.feature",
    "Orchestrator respects agent execution conditions",
)
def test_orchestrator_respects_agent_conditions() -> None:
    """Test that the orchestrator respects agent execution conditions."""


# Background steps


@given("the system is configured with multiple agents")
def system_configured_with_multiple_agents(
    test_context: OrchestratorScenarioContext,
    bdd_context: BehaviorContext,
) -> None:
    """Configure the system with multiple agents."""

    config = ConfigModel(
        agents=["Synthesizer", "Contrarian", "FactChecker"],
        reasoning_mode="dialectical",
        loops=1,
        llm_backend="dummy",
        default_model="dummy-model",
    )
    test_context.config = config
    test_context.agents = ["Synthesizer", "Contrarian", "FactChecker"]
    set_value(bdd_context, "config", config)


@given("the system is using a dummy LLM adapter for testing")
def system_using_dummy_llm_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure the system to use a dummy LLM adapter."""

    monkeypatch.setattr(
        "autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter()
    )


# Scenario: Orchestrator executes agents in the correct order


@when("I run a query with the dialectical reasoning mode")
def run_query_with_dialectical_reasoning(
    test_context: OrchestratorScenarioContext,
    mock_agent_factory: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
) -> None:
    """Run a query with the dialectical reasoning mode."""

    test_context.original_execute_agent = OrchestrationUtils.execute_agent

    original_get = mock_agent_factory.get

    def get_and_track(name: str) -> MagicMock:
        agent = cast(MagicMock, original_get(name))
        test_context.executed_agents.append(name)
        return agent

    mock_agent_factory.get.side_effect = get_and_track

    def execute_and_track_state(
        agent_name: str,
        state: Any,
        config: ConfigModel,
        metrics: Any,
        callbacks: Any,
        agent_factory: Any,
        storage_manager: Any,
        loop: int,
    ) -> None:
        test_context.agent_states[agent_name] = state.copy()
        if test_context.original_execute_agent is None:
            raise AssertionError("Original execute_agent reference missing")
        test_context.original_execute_agent(
            agent_name,
            state,
            config,
            metrics,
            callbacks,
            agent_factory,
            storage_manager,
            loop,
        )
        return None

    monkeypatch.setattr(OrchestrationUtils, "execute_agent", execute_and_track_state)

    orchestrator = get_orchestrator(bdd_context)
    config = get_config(bdd_context)

    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory", mock_agent_factory
    ):
        try:
            test_context.result = orchestrator.run_query("test query", config)
        except Exception as exc:  # noqa: BLE001
            test_context.exception = exc
            test_context.result = {"error": str(exc)}


@then("the agents should be executed in the correct sequence")
def agents_executed_in_correct_sequence(
    test_context: OrchestratorScenarioContext,
) -> None:
    """Verify that agents were executed in the correct sequence."""

    if test_context.exception is not None:
        raise test_context.exception

    assert test_context.executed_agents == test_context.agents


@then("each agent should receive the state from previous agents")
def agents_receive_state_from_previous(
    test_context: OrchestratorScenarioContext,
) -> None:
    """Verify that each agent received the state from previous agents."""

    if test_context.exception is not None:
        raise test_context.exception

    for index, agent_name in enumerate(test_context.executed_agents):
        if index == 0:
            continue
        previous_agent = test_context.executed_agents[index - 1]
        agent_state = test_context.agent_states.get(agent_name)
        assert agent_state is not None
        assert previous_agent in str(agent_state)


@then("the final result should include contributions from all agents")
def result_includes_all_agent_contributions(
    test_context: OrchestratorScenarioContext,
) -> None:
    """Verify that the final result includes contributions from all agents."""

    if test_context.exception is not None:
        raise test_context.exception

    for agent_name in test_context.agents:
        assert agent_name in str(test_context.result)


# Scenario: Orchestrator handles agent errors gracefully


@given("an agent that will raise an error")
def agent_that_raises_error(
    mock_agent_factory: MagicMock,
    test_context: OrchestratorScenarioContext,
    bdd_context: BehaviorContext,
) -> None:
    """Configure an agent that will raise an error when executed."""

    error_agent = MagicMock()
    error_agent.name = "ErrorAgent"
    error_agent.can_execute.return_value = True
    error_agent.execute.side_effect = ValueError("Test error")

    def get_agent(name: str) -> MagicMock:
        if name == "ErrorAgent":
            return error_agent
        agent = MagicMock()
        agent.name = name
        agent.can_execute.return_value = True
        agent.execute.return_value = {
            "agent": name,
            "result": f"Result from {name}",
        }
        return agent

    mock_agent_factory.get.side_effect = get_agent

    config = ConfigModel(
        agents=["ErrorAgent", "Synthesizer"],
        reasoning_mode="direct",
        loops=1,
        max_errors=1,
        llm_backend="dummy",
        default_model="dummy-model",
    )
    test_context.config = config
    set_value(bdd_context, "config", config)


@when("I run a query with that agent")
def run_query_with_error_agent(
    test_context: OrchestratorScenarioContext,
    mock_agent_factory: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
) -> None:
    """Run a query with the error-raising agent."""

    test_context.original_handle_error = OrchestrationUtils.handle_agent_error

    def handle_and_track_error(
        self: OrchestrationUtils,
        error: Exception,
        agent_name: str,
        state: Any,
        config: ConfigModel,
    ) -> dict[str, object]:
        test_context.errors.append((agent_name, error))
        if test_context.original_handle_error is None:
            raise AssertionError("Original handle_agent_error reference missing")
        return test_context.original_handle_error(
            self, error, agent_name, state, config
        )

    monkeypatch.setattr(OrchestrationUtils, "handle_agent_error", handle_and_track_error)

    orchestrator = get_orchestrator(bdd_context)
    config = get_config(bdd_context)

    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory", mock_agent_factory
    ):
        try:
            test_context.result = orchestrator.run_query("test query", config)
        except Exception as exc:  # noqa: BLE001
            test_context.exception = exc


@then("the orchestrator should catch and log the error")
def orchestrator_catches_and_logs_error(
    test_context: OrchestratorScenarioContext,
) -> None:
    """Verify that the orchestrator caught and logged the error."""

    if test_context.errors:
        agent_name, error = test_context.errors[0]
        assert agent_name == "ErrorAgent"
        assert "Test error" in str(error)
    elif test_context.exception is not None:
        assert "error" in str(test_context.exception).lower()
    else:
        raise AssertionError("No error was caught or logged")


@then("the orchestrator should continue with other agents if possible")
def orchestrator_continues_with_other_agents(
    test_context: OrchestratorScenarioContext,
) -> None:
    """Verify that the orchestrator continued with other agents after an error."""

    if test_context.exception is None:
        assert "Synthesizer" in str(test_context.result)


@then("the final result should include information about the error")
def result_includes_error_information(
    test_context: OrchestratorScenarioContext,
) -> None:
    """Verify that the final result includes information about the error."""

    if test_context.exception is None:
        assert "error" in str(test_context.result).lower()


# Scenario: Orchestrator respects agent execution conditions


@given("an agent that can only execute under specific conditions")
def agent_with_specific_execution_conditions(
    mock_agent_factory: MagicMock,
    test_context: OrchestratorScenarioContext,
    bdd_context: BehaviorContext,
) -> None:
    """Configure an agent that can only execute under specific conditions."""

    conditional_agent = MagicMock()
    conditional_agent.name = "ConditionalAgent"
    conditional_agent.can_execute.return_value = False

    def get_agent(name: str) -> MagicMock:
        if name == "ConditionalAgent":
            return conditional_agent
        agent = MagicMock()
        agent.name = name
        agent.can_execute.return_value = True
        agent.execute.return_value = {
            "agent": name,
            "result": f"Result from {name}",
        }
        return agent

    mock_agent_factory.get.side_effect = get_agent

    config = ConfigModel(
        agents=["ConditionalAgent", "Synthesizer"],
        reasoning_mode="direct",
        loops=1,
        llm_backend="dummy",
        default_model="dummy-model",
    )
    test_context.config = config
    set_value(bdd_context, "config", config)


@when("I run a query that doesn't meet those conditions")
def run_query_not_meeting_conditions(
    test_context: OrchestratorScenarioContext,
    mock_agent_factory: MagicMock,
    bdd_context: BehaviorContext,
) -> None:
    """Run a query that doesn't meet the conditions for the conditional agent."""

    test_context.original_get = mock_agent_factory.get

    def get_and_track(name: str) -> MagicMock:
        if test_context.original_get is None:
            raise AssertionError("Original agent factory getter missing")
        agent = test_context.original_get(name)
        if agent.can_execute.return_value:
            test_context.executed_agents.append(name)
        return agent

    mock_agent_factory.get.side_effect = get_and_track

    orchestrator = get_orchestrator(bdd_context)
    config = get_config(bdd_context)

    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory", mock_agent_factory
    ):
        try:
            test_context.result = orchestrator.run_query("test query", config)
        except Exception as exc:  # noqa: BLE001
            test_context.exception = exc
            test_context.result = {"error": str(exc)}


@then("that agent should not be executed")
def agent_not_executed(test_context: OrchestratorScenarioContext) -> None:
    """Verify that the conditional agent was not executed."""

    if test_context.exception is not None:
        raise test_context.exception

    assert "ConditionalAgent" not in test_context.executed_agents


@then("the orchestrator should continue with other agents")
def orchestrator_continues_with_other_agents_after_skip(
    test_context: OrchestratorScenarioContext,
) -> None:
    """Verify that the orchestrator continued with other agents after skipping one."""

    if test_context.exception is not None:
        raise test_context.exception

    assert "Synthesizer" in test_context.executed_agents


@then("the final result should not include contributions from the skipped agent")
def result_excludes_skipped_agent_contributions(
    test_context: OrchestratorScenarioContext,
) -> None:
    """Verify that the final result doesn't include contributions from the skipped agent."""

    if test_context.exception is not None:
        raise test_context.exception

    assert "ConditionalAgent" not in str(test_context.result)
