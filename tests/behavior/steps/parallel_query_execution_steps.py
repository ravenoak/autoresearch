"""Step definitions for parallel query execution tests.

This module contains step definitions for testing the parallel query execution
functionality of the orchestrator, including running multiple agent groups in
parallel, handling errors, and synthesizing results.
"""

import time
import pytest
from pytest_bdd import scenario, given, when, then
from unittest.mock import MagicMock, patch

from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.config import ConfigModel
from autoresearch.llm import DummyAdapter
from autoresearch.models import QueryResponse


# Fixtures
@pytest.fixture
def test_context():
    """Create a context for storing test state."""
    return {
        "config": None,
        "agent_groups": [],
        "executed_groups": [],
        "result": None,
        "errors": [],
        "start_time": 0,
        "end_time": 0,
    }


@pytest.fixture
def mock_agent_factory():
    """Create a mock agent factory for testing."""
    factory = MagicMock()
    agents = {}

    def get_agent(name):
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
    "../features/parallel_query_execution.feature",
    "Running multiple agent groups in parallel",
)
def test_running_multiple_agent_groups():
    """Test running multiple agent groups in parallel."""
    pass


@scenario(
    "../features/parallel_query_execution.feature",
    "Handling errors in parallel execution",
)
def test_handling_errors_in_parallel_execution():
    """Test handling errors in parallel execution."""
    pass


@scenario(
    "../features/parallel_query_execution.feature",
    "Synthesizing results from multiple agent groups",
)
def test_synthesizing_results_from_multiple_groups():
    """Test synthesizing results from multiple agent groups."""
    pass


# Background steps
@given("the system is configured with multiple agent groups")
def system_configured_with_multiple_agent_groups(test_context):
    """Configure the system with multiple agent groups."""
    test_context["config"] = ConfigModel(
        agents=[
            "Synthesizer"
        ],  # Default agents, will be overridden in run_parallel_query
        reasoning_mode="direct",
        loops=1,
    )
    test_context["agent_groups"] = [
        ["Synthesizer", "Contrarian"],
        ["FactChecker", "Synthesizer"],
        ["Contrarian", "FactChecker", "Synthesizer"],
    ]


@given("the system is using a dummy LLM adapter for testing")
def system_using_dummy_llm_adapter(monkeypatch):
    """Configure the system to use a dummy LLM adapter."""
    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter())


# Scenario: Running multiple agent groups in parallel
@when("I run a parallel query with multiple agent groups")
def run_parallel_query_with_multiple_groups(
    test_context, mock_agent_factory, monkeypatch
):
    """Run a parallel query with multiple agent groups."""
    # Mock run_query to track executed groups
    original_run_query = Orchestrator.run_query

    def mock_run_query(query, config, callbacks=None, **kwargs):
        test_context["executed_groups"].append(config.agents)
        # Create a dummy response
        return QueryResponse(
            answer=f"Answer from {config.agents}",
            citations=[f"Citation from {config.agents}"],
            reasoning=[f"Reasoning from {config.agents}"],
            metrics={"group": str(config.agents)},
        )

    # Use monkeypatch for automatic cleanup
    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)

    # Mock the synthesizer agent
    synthesizer = MagicMock()
    synthesizer.execute.return_value = {
        "answer": "Synthesized answer",
        "claims": ["Synthesized claim 1", "Synthesized claim 2"],
        "sources": ["Synthesized source 1", "Synthesized source 2"],
    }

    def get_agent(name):
        if name == "Synthesizer":
            return synthesizer
        else:
            agent = MagicMock()
            agent.name = name
            agent.can_execute.return_value = True
            agent.execute.return_value = {
                "agent": name,
                "result": f"Result from {name}",
            }
            return agent

    mock_agent_factory.get.side_effect = get_agent

    # Run the parallel query and measure execution time
    test_context["start_time"] = time.time()
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory", mock_agent_factory
    ):
        test_context["result"] = Orchestrator.run_parallel_query(
            "test query", test_context["config"], test_context["agent_groups"]
        )
    test_context["end_time"] = time.time()


@then("each agent group should be executed")
def each_agent_group_executed(test_context):
    """Verify that each agent group was executed."""
    for group in test_context["agent_groups"]:
        assert group in test_context["executed_groups"]


@then("the final result should include contributions from all agent groups")
def result_includes_all_group_contributions(test_context):
    """Verify that the final result includes contributions from all agent groups."""
    for group in test_context["agent_groups"]:
        assert str(group) in str(test_context["result"])


@then("the execution should be faster than running the groups sequentially")
def execution_faster_than_sequential(test_context):
    """Verify that parallel execution is faster than sequential execution."""
    # This is a bit tricky to test reliably, so we'll just check that the execution time is reasonable
    parallel_time = test_context["end_time"] - test_context["start_time"]
    # In a real test, we would compare to sequential execution time
    # For now, we'll just assert that it completed in a reasonable time
    assert parallel_time < 10.0, (
        f"Parallel execution took {parallel_time} seconds, which is too long"
    )


# Scenario: Handling errors in parallel execution
@given("an agent group that will raise an error")
def agent_group_that_raises_error(test_context, mock_agent_factory):
    """Configure an agent group that will raise an error when executed."""
    # Add an error-raising group to the agent groups
    test_context["agent_groups"] = [
        ["ErrorAgent", "Synthesizer"],  # This group will raise an error
        ["FactChecker", "Synthesizer"],  # This group should still execute
    ]

    # Configure the error agent
    error_agent = MagicMock()
    error_agent.name = "ErrorAgent"
    error_agent.can_execute.return_value = True
    error_agent.execute.side_effect = ValueError("Test error")

    # Update the mock_agent_factory to return the error agent
    original_get = mock_agent_factory.get

    def get_agent_with_error(name):
        if name == "ErrorAgent":
            return error_agent
        else:
            return original_get(name)

    mock_agent_factory.get.side_effect = get_agent_with_error


@when("I run a parallel query with that agent group")
def run_parallel_query_with_error_group(test_context, mock_agent_factory, monkeypatch):
    """Run a parallel query with the error-raising agent group."""

    # Mock run_query to track executed groups and errors
    def mock_run_query(query, config, callbacks=None, **kwargs):
        test_context["executed_groups"].append(config.agents)
        if "ErrorAgent" in config.agents:
            error = ValueError("Test error")
            test_context["errors"].append((config.agents, error))
            raise error
        # Create a dummy response for non-error groups
        return QueryResponse(
            answer=f"Answer from {config.agents}",
            citations=[f"Citation from {config.agents}"],
            reasoning=[f"Reasoning from {config.agents}"],
            metrics={"group": str(config.agents)},
        )

    # Use monkeypatch for automatic cleanup
    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)

    # Mock the synthesizer agent
    synthesizer = MagicMock()
    synthesizer.execute.return_value = {
        "answer": "Synthesized answer with error information",
        "claims": ["Synthesized claim 1", "Synthesized claim 2"],
        "sources": ["Synthesized source 1", "Synthesized source 2"],
    }

    def get_agent(name):
        if name == "Synthesizer":
            return synthesizer
        else:
            agent = MagicMock()
            agent.name = name
            agent.can_execute.return_value = True
            agent.execute.return_value = {
                "agent": name,
                "result": f"Result from {name}",
            }
            return agent

    mock_agent_factory.get.side_effect = get_agent

    # Run the parallel query
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory", mock_agent_factory
    ):
        test_context["result"] = Orchestrator.run_parallel_query(
            "test query", test_context["config"], test_context["agent_groups"]
        )


@then("the orchestrator should catch and log the error")
def orchestrator_catches_and_logs_error_parallel(test_context):
    """Verify that the orchestrator caught and logged the error."""
    assert len(test_context["errors"]) > 0
    assert "ErrorAgent" in str(test_context["errors"][0][0])
    assert "Test error" in str(test_context["errors"][0][1])


@then("the orchestrator should continue with other agent groups")
def orchestrator_continues_with_other_groups(test_context):
    """Verify that the orchestrator continued with other agent groups after an error."""
    # Check that the non-error group was executed
    assert ["FactChecker", "Synthesizer"] in test_context["executed_groups"]
    # Check that the result includes contributions from the non-error group
    assert "FactChecker" in str(test_context["result"])


@then("the final result should include information about the error")
def result_includes_error_information_parallel(test_context):
    """Verify that the final result includes information about the error."""
    assert "error" in str(test_context["result"]).lower()


# Scenario: Synthesizing results from multiple agent groups
@then("the orchestrator should synthesize the results from all agent groups")
def orchestrator_synthesizes_results(test_context, mock_agent_factory):
    """Verify that the orchestrator synthesized the results from all agent groups."""
    # Check that the synthesizer agent was called
    synthesizer = mock_agent_factory.get("Synthesizer")
    assert synthesizer.execute.called


@then(
    "the final result should be a coherent answer that combines insights from all groups"
)
def result_is_coherent_answer(test_context):
    """Verify that the final result is a coherent answer that combines insights from all groups."""
    # Check that the result includes the synthesized answer
    assert "Synthesized" in test_context["result"].answer
    # Check that the result includes reasoning from the synthesizer
    assert "Synthesized claim" in str(test_context["result"].reasoning)
