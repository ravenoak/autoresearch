# mypy: ignore-errors
"""Step definitions for extended orchestrator and agents integration tests.

This module contains step definitions for testing the extended integration between
the orchestrator and agents, including multiple loops, different reasoning modes,
and agent state persistence.
"""
from __future__ import annotations
from tests.behavior.utils import as_payload

from typing import Any, Callable, MutableMapping, cast

import pytest
from pytest_bdd import given, scenario, then, when
from unittest.mock import MagicMock, patch

from autoresearch.config.models import ConfigModel
from autoresearch.llm import DummyAdapter
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils

ExtendedTestContext = MutableMapping[str, Any]


# Background step definitions
@given("the system is configured with multiple agents")
def system_configured_with_multiple_agents(
    extended_test_context: ExtendedTestContext,
) -> None:
    """Configure the system with multiple agents."""
    extended_test_context["config"] = ConfigModel(
        agents=["Synthesizer", "Contrarian", "FactChecker"],
        reasoning_mode="dialectical",
        loops=1,
        llm_backend="dummy",
        default_model="dummy-model",
    )
    extended_test_context["agents"] = ["Synthesizer", "Contrarian", "FactChecker"]


@given("the system is using a dummy LLM adapter for testing")
def system_using_dummy_llm_adapter(
    extended_test_context: ExtendedTestContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Configure the system to use a dummy LLM adapter for testing."""
    # Create a patch for the LLM adapter factory to return a dummy adapter
    mock_llm_adapter = MagicMock(spec=DummyAdapter)
    mock_llm_adapter.generate.return_value = "Dummy response from LLM"

    # Store the mock adapter in the test context for later verification
    extended_test_context["llm_adapter"] = mock_llm_adapter

    # Create a patch for the LLM adapter factory using monkeypatch
    monkeypatch.setattr(
        "autoresearch.llm.get_llm_adapter", lambda *args, **kwargs: mock_llm_adapter
    )


# Fixtures
@pytest.fixture
def extended_test_context() -> ExtendedTestContext:
    """Create a context for storing test state."""
    return as_payload({
        "config": None,
        "agents": [],
        "executed_agents": [],
        "agent_states": {},
        "loop_executions": {},
        "result": None,
        "errors": [],
    })


# Scenarios
@pytest.mark.slow
@scenario(
    "../features/orchestrator_agents_integration_extended.feature",
    "Orchestrator executes multiple loops correctly",
)
def test_orchestrator_executes_multiple_loops() -> None:
    """Test that the orchestrator executes multiple loops correctly."""
    pass


@pytest.mark.slow
@scenario(
    "../features/orchestrator_agents_integration_extended.feature",
    "Orchestrator supports different reasoning modes",
)
def test_orchestrator_supports_different_reasoning_modes() -> None:
    """Test that the orchestrator supports different reasoning modes."""
    pass


@pytest.mark.slow
@scenario(
    "../features/orchestrator_agents_integration_extended.feature",
    "Orchestrator preserves agent state between loops",
)
def test_orchestrator_preserves_agent_state() -> None:
    """Test that the orchestrator preserves agent state between loops."""
    pass


# Step definitions for "Orchestrator executes multiple loops correctly"
@given("the system is configured to run multiple reasoning loops")
def system_configured_for_multiple_loops(
    extended_test_context: ExtendedTestContext,
) -> None:
    """Configure the system to run multiple reasoning loops."""
    extended_test_context["config"] = ConfigModel(
        agents=["Synthesizer", "Contrarian", "FactChecker"],
        reasoning_mode="dialectical",
        loops=3,  # Run 3 loops
        llm_backend="dummy",
        default_model="dummy-model",
    )
    extended_test_context["agents"] = ["Synthesizer", "Contrarian", "FactChecker"]


@when("I run a query with multiple loops")
def run_query_with_multiple_loops(
    extended_test_context: ExtendedTestContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run a query with multiple loops."""
    # Store original functions for cleanup verification
    original_execute_agent: Callable[..., None] = OrchestrationUtils.execute_agent
    extended_test_context["original_execute_agent"] = original_execute_agent

    # Track executed agents by loop
    mock_agent_factory = MagicMock()
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

    mock_agent_factory.get.side_effect = get_agent

    # Track agent executions by loop
    def execute_and_track_state(
        agent_name: str,
        state: dict[str, Any],
        config: ConfigModel,
        metrics: Any,
        callbacks: Any,
        agent_factory: Any,
        storage_manager: Any,
        loop: int,
    ) -> None:
        # Track which agents were executed in which loop
        loop_executions = cast(dict[int, list[str]], extended_test_context["loop_executions"])
        loop_agents = loop_executions.setdefault(loop, [])
        loop_agents.append(agent_name)

        # Track the state for each agent in each loop
        key = f"{agent_name}_{loop}"
        agent_states = cast(dict[str, dict[str, Any]], extended_test_context["agent_states"])
        agent_states[key] = state.copy()

        # Track all executed agents
        executed_agents = cast(
            list[str], extended_test_context.setdefault("executed_agents", [])
        )
        executed_agents.append(agent_name)

        # Call the original function
        original = cast(
            Callable[..., None], extended_test_context["original_execute_agent"]
        )
        original(
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

    # Use monkeypatch for automatic cleanup
    monkeypatch.setattr(OrchestrationUtils, "execute_agent", execute_and_track_state)

    # Run the query
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory", mock_agent_factory
    ):
        config = extended_test_context.get("config")
        orchestrator = Orchestrator()
        try:
            if isinstance(config, ConfigModel):
                extended_test_context["result"] = orchestrator.run_query("test query", config)
            else:
                raise TypeError("Scenario context missing ConfigModel configuration")
        except Exception as exc:
            extended_test_context["exception"] = exc
            # Store the exception as the result for testing
            extended_test_context["result"] = {"error": str(exc)}


@then("each loop should execute the agents in the correct sequence")
def each_loop_executes_agents_in_correct_sequence(
    extended_test_context: ExtendedTestContext,
) -> None:
    """Verify that each loop executes the agents in the correct sequence."""
    # Surface any error captured during execution
    exc = extended_test_context.get("exception")
    if isinstance(exc, Exception):
        raise exc

    # Verify that we have the expected number of loops
    loop_executions = cast(dict[int, list[str]], extended_test_context["loop_executions"])
    assert len(loop_executions) == 3, (
        "Should have executed 3 loops"
    )

    # Verify that each loop executed the agents in the correct sequence
    expected_sequence = cast(list[str], extended_test_context["agents"])
    for loop, agents in loop_executions.items():
        assert agents == expected_sequence, (
            f"Loop {loop} did not execute agents in the correct sequence"
        )


@then("the state should be preserved between loops")
def state_preserved_between_loops(extended_test_context: ExtendedTestContext) -> None:
    """Verify that the state is preserved between loops."""
    # Surface any error captured during execution
    exc = extended_test_context.get("exception")
    if isinstance(exc, Exception):
        raise exc

    # Verify that the state from the last agent in loop 1 is passed to the first agent in loop 2
    loop_executions = cast(dict[int, list[str]], extended_test_context["loop_executions"])
    last_agent_loop1 = loop_executions[1][-1]
    first_agent_loop2 = loop_executions[2][0]

    agent_states = cast(dict[str, dict[str, Any]], extended_test_context["agent_states"])
    last_agent_state = agent_states[f"{last_agent_loop1}_1"]
    first_agent_state = agent_states[f"{first_agent_loop2}_2"]

    # The state should be preserved (at least contain the same keys)
    for key in last_agent_state:
        assert key in first_agent_state, (
            f"State key {key} was not preserved between loops"
        )


@then("the final result should include contributions from all loops")
def result_includes_all_loop_contributions(
    extended_test_context: ExtendedTestContext,
) -> None:
    """Verify that the final result includes contributions from all loops."""
    # Surface any error captured during execution
    exc = extended_test_context.get("exception")
    if isinstance(exc, Exception):
        raise exc

    # The result should include all agents from all loops
    result_str = str(extended_test_context.get("result"))
    for loop in range(1, 4):  # Loops 1, 2, 3
        for agent in cast(list[str], extended_test_context["agents"]):
            assert agent in result_str, (
                f"Result should include agent {agent} from loop {loop}"
            )


# Step definitions for "Orchestrator supports different reasoning modes"
@given('the system is configured with the "direct" reasoning mode')
def system_configured_with_direct_reasoning_mode(
    extended_test_context: ExtendedTestContext,
) -> None:
    """Configure the system with the direct reasoning mode."""
    extended_test_context["config"] = ConfigModel(
        agents=["Synthesizer", "Contrarian", "FactChecker"],
        reasoning_mode="direct",  # Use direct reasoning mode
        loops=1,
        llm_backend="dummy",
        default_model="dummy-model",
    )
    extended_test_context["agents"] = ["Synthesizer", "Contrarian", "FactChecker"]
    extended_test_context["primary_agent"] = (
        "Synthesizer"  # The primary agent in direct mode
    )


@when("I run a query with the direct reasoning mode")
def run_query_with_direct_reasoning_mode(
    extended_test_context: ExtendedTestContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run a query with the direct reasoning mode."""
    # Store original functions for cleanup verification
    original_execute_agent: Callable[..., None] = OrchestrationUtils.execute_agent
    extended_test_context["original_execute_agent"] = original_execute_agent

    # Track executed agents
    mock_agent_factory = MagicMock()
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

    mock_agent_factory.get.side_effect = get_agent

    # Track agent executions
    def execute_and_track_state(
        agent_name: str,
        state: dict[str, Any],
        config: ConfigModel,
        metrics: Any,
        callbacks: Any,
        agent_factory: Any,
        storage_manager: Any,
        loop: int,
    ) -> None:
        executed_agents = cast(
            list[str], extended_test_context.setdefault("executed_agents", [])
        )
        executed_agents.append(agent_name)
        agent_states = cast(dict[str, dict[str, Any]], extended_test_context["agent_states"])
        agent_states[agent_name] = state.copy()
        original = cast(
            Callable[..., None], extended_test_context["original_execute_agent"]
        )
        original(
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

    # Use monkeypatch for automatic cleanup
    monkeypatch.setattr(OrchestrationUtils, "execute_agent", execute_and_track_state)

    # Run the query
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory", mock_agent_factory
    ):
        config = extended_test_context.get("config")
        orchestrator = Orchestrator()
        try:
            if isinstance(config, ConfigModel):
                extended_test_context["result"] = orchestrator.run_query("test query", config)
            else:
                raise TypeError("Scenario context missing ConfigModel configuration")
        except Exception as exc:
            extended_test_context["exception"] = exc
            extended_test_context["result"] = {"error": str(exc)}


@then("only the primary agent should be executed")
def only_primary_agent_executed(extended_test_context: ExtendedTestContext) -> None:
    """Verify that only the primary agent was executed."""
    # Surface any error captured during execution
    exc = extended_test_context.get("exception")
    if isinstance(exc, Exception):
        raise exc

    # In direct mode, only the primary agent (Synthesizer) should be executed
    executed_agents = cast(list[str], extended_test_context.get("executed_agents", []))
    assert len(executed_agents) == 1, (
        "Only one agent should be executed in direct mode"
    )
    assert (
        executed_agents[0]
        == extended_test_context["primary_agent"]
    ), (
        f"The primary agent ({extended_test_context['primary_agent']}) should be the only one executed"
    )


@then("the final result should include only the primary agent's contribution")
def result_includes_only_primary_agent_contribution(
    extended_test_context: ExtendedTestContext,
) -> None:
    """Verify that the final result includes only the primary agent's contribution."""
    # Surface any error captured during execution
    exc = extended_test_context.get("exception")
    if isinstance(exc, Exception):
        raise exc

    # The result should include only the primary agent
    result_str = str(extended_test_context.get("result"))
    primary_agent = cast(str, extended_test_context["primary_agent"])
    assert primary_agent in result_str, (
        f"Result should include the primary agent ({extended_test_context['primary_agent']})"
    )

    # The result should not include other agents
    for agent in cast(list[str], extended_test_context["agents"]):
        if agent != primary_agent:
            assert (
                agent not in result_str or f"Result from {agent}" not in result_str
            ), f"Result should not include agent {agent}"


# Step definitions for "Orchestrator preserves agent state between loops"
@given("an agent that modifies the state in a specific way")
def agent_that_modifies_state(
    extended_test_context: ExtendedTestContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Configure an agent that modifies the state in a specific way."""
    # Create a mock agent that modifies the state
    state_modifying_agent = MagicMock()
    state_modifying_agent.name = "StateModifier"
    state_modifying_agent.can_execute.return_value = True

    # This agent will add a counter to the state and increment it each time it's called
    def execute_with_state_modification(query: str, state: dict[str, Any]) -> dict[str, Any]:
        if "counter" not in state:
            state["counter"] = 1
        else:
            state["counter"] += 1
        return as_payload({
            "agent": "StateModifier",
            "result": f"Result from StateModifier (counter: {state['counter']})",
            "counter": state["counter"],
        })

    state_modifying_agent.execute.side_effect = execute_with_state_modification

    # Replace the Synthesizer agent with our state-modifying agent
    extended_test_context["agents"] = ["StateModifier", "Contrarian", "FactChecker"]
    extended_test_context["config"] = ConfigModel(
        agents=extended_test_context["agents"],
        reasoning_mode="dialectical",
        loops=3,  # Run 3 loops
        llm_backend="dummy",
        default_model="dummy-model",
    )

    # Store the agent for later use
    extended_test_context["state_modifying_agent"] = state_modifying_agent


@then("the state modifications should be preserved between loops")
def state_modifications_preserved_between_loops(
    extended_test_context: ExtendedTestContext,
) -> None:
    """Verify that state modifications are preserved between loops."""
    # Surface any error captured during execution
    exc = extended_test_context.get("exception")
    if isinstance(exc, Exception):
        raise exc

    # Verify that the counter was incremented in each loop
    for loop in range(1, 4):  # Loops 1, 2, 3
        agent_key = f"StateModifier_{loop}"
        agent_states = cast(dict[str, dict[str, Any]], extended_test_context["agent_states"])
        if agent_key in agent_states:
            state = agent_states[agent_key]
            assert "counter" in state, f"Counter should be in state for loop {loop}"
            assert state["counter"] == loop, (
                f"Counter should be {loop} in loop {loop}, got {state['counter']}"
            )


@then("the final result should reflect the cumulative state changes")
def result_reflects_cumulative_state_changes(
    extended_test_context: ExtendedTestContext,
) -> None:
    """Verify that the final result reflects the cumulative state changes."""
    # Surface any error captured during execution
    exc = extended_test_context.get("exception")
    if isinstance(exc, Exception):
        raise exc

    # The result should include the final counter value
    result_str = str(extended_test_context.get("result"))
    assert "counter: 3" in result_str, (
        "Result should include the final counter value (3)"
    )
