"""Tests for error handling in the orchestration system.

This module contains tests for various error scenarios in the orchestration system,
including agent execution errors, invalid agent names, and callback errors.
"""

import pytest
from unittest.mock import MagicMock

from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.errors import OrchestrationError
from autoresearch.config import ConfigModel


# Fixtures for common test setup
@pytest.fixture
def test_config():
    """Create a test configuration with minimal settings."""
    return ConfigModel(agents=["TestAgent"], loops=1, max_errors=1)


@pytest.fixture
def failing_agent():
    """Create a failing agent that raises an exception when executed."""
    agent = MagicMock()
    agent.can_execute.return_value = True
    agent.execute.side_effect = ValueError("boom")
    return agent


def test_orchestrator_raises_after_error(monkeypatch, test_config, failing_agent):
    """Test that the orchestrator raises an OrchestrationError after an agent error.

    This test verifies that when an agent raises an exception during execution,
    the orchestrator properly wraps it in an OrchestrationError and includes
    the original error in the context.
    """
    # Setup
    test_config.agents = ["FailingAgent"]

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        lambda name: failing_agent,
    )

    # Execute and Verify
    with pytest.raises(OrchestrationError) as excinfo:
        Orchestrator.run_query("test query", test_config)

    # Verify the error contains the agent errors
    assert excinfo.value.context.get("errors") is not None
    assert len(excinfo.value.context["errors"]) > 0


def test_invalid_agent_name_raises(test_config):
    """Test that using an invalid agent name raises an OrchestrationError.

    This test verifies that when an unknown agent name is specified in the
    configuration, the orchestrator raises an OrchestrationError with
    appropriate error information in the context.
    """
    # Setup
    test_config.agents = ["Unknown"]

    # Execute and Verify
    with pytest.raises(OrchestrationError) as excinfo:
        Orchestrator.run_query("test query", test_config)

    # Verify the error contains the agent errors
    assert excinfo.value.context.get("errors") is not None
    errors = excinfo.value.context["errors"]
    assert len(errors) > 0

    # Check that one of the errors is about the unknown agent
    error_messages = [str(error.get("error", "")) for error in errors]
    assert any("Unknown" in msg and "agent" in msg.lower() for msg in error_messages)


def test_callback_error_propagates(test_config):
    """Test that errors in callbacks propagate to the caller.

    This test verifies that when a callback function raises an exception,
    the exception is not caught by the orchestrator but propagates to the caller.
    This ensures that callback errors are visible and not silently ignored.
    """

    # Setup
    def bad_callback(*args, **kwargs):
        raise RuntimeError("boom")

    # Execute and Verify
    with pytest.raises(RuntimeError):
        Orchestrator.run_query(
            "test query",
            test_config,
            callbacks={"on_cycle_start": bad_callback},
        )


@pytest.mark.parametrize(
    "error_type, error_message",
    [
        (ValueError, "specific error"),
        (RuntimeError, "runtime error"),
        (KeyError, "missing key"),
    ],
)
def test_agent_error_is_wrapped(monkeypatch, test_config, error_type, error_message):
    """Test that agent errors are wrapped in AgentError.

    This test verifies that when an agent raises an exception during execution,
    the orchestrator properly wraps it in an AgentError and includes it in the
    OrchestrationError context. This is tested with different error types to
    ensure consistent behavior.

    Args:
        monkeypatch: Pytest fixture for patching
        test_config: Test configuration fixture
        error_type: The type of error to raise
        error_message: The error message to include
    """
    # Setup
    test_config.agents = ["FailingAgent"]

    # Create a failing agent with the specified error type and message
    agent = MagicMock()
    agent.can_execute.return_value = True
    agent.execute.side_effect = error_type(error_message)

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        lambda name: agent,
    )

    # Execute and Verify
    with pytest.raises(OrchestrationError) as excinfo:
        Orchestrator.run_query("test query", test_config)

    # Verify the error contains agent errors
    assert excinfo.value.context.get("errors") is not None
    errors = excinfo.value.context["errors"]
    assert len(errors) > 0

    # At least one error should be an AgentError and contain the original error message
    error_strings = [str(error) for error in errors]
    assert any("agent" in error.lower() for error in error_strings)
    assert any(error_message in error for error in error_strings)
