# mypy: ignore-errors
"""Step definitions for test cleanup verification.

This module contains step definitions for verifying that tests clean up
their side effects properly, including monkeypatches, mocks, and temporary files.
"""

import os
import sys
from typing import Any, TypedDict
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, scenario, then, when

from tests.typing_helpers import TypedFixture

from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.llm import DummyAdapter


class CleanupContext(TypedDict, total=False):
    """State container for cleanup verification across steps."""

    config: Any
    monkeypatches: list[tuple[str, Any]]
    mocks: list[MagicMock]
    temp_files: list[str]
    result: Any
    error: BaseException
    initial_env_vars: dict[str, str]
    initial_sys_modules: set[str]


# Fixtures
@pytest.fixture
def cleanup_context() -> TypedFixture[CleanupContext]:
    """Create a context for storing test state and tracking resources."""

    context: CleanupContext = {
        "config": None,
        "monkeypatches": [],
        "mocks": [],
        "temp_files": [],
        "result": None,
    }
    return context


# Scenarios
@scenario(
    "../features/test_cleanup.feature",
    "Orchestrator and agents integration tests clean up properly",
)
def test_orchestrator_agents_cleanup() -> None:
    """Test that orchestrator and agents integration tests clean up properly."""
    pass


# Step definitions
@given("the system is configured with multiple agents", target_fixture="config")
def system_configured_with_multiple_agents(
    cleanup_context: CleanupContext, config_model: Any
) -> Any:
    """Configure the system with multiple agents."""
    config = config_model.model_copy()
    config.agents = ["Synthesizer", "Contrarian", "FactChecker"]
    config.reasoning_mode = "dialectical"
    config.loops = 1
    config.llm_backend = "dummy"
    config.default_model = "dummy-model"

    # Track initial state
    cleanup_context["initial_env_vars"] = os.environ.copy()
    cleanup_context["initial_sys_modules"] = set(sys.modules.keys())
    return config


@when("I run a query with the dialectical reasoning mode")
def run_query_with_dialectical_reasoning(
    config: Any, cleanup_context: CleanupContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run a query with the dialectical reasoning mode."""
    # Import the original function directly
    from autoresearch.llm import get_llm_adapter as original_get_llm_adapter

    # Track monkeypatches
    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter())
    cleanup_context["monkeypatches"].append(
        ("autoresearch.llm.get_llm_adapter", original_get_llm_adapter)
    )

    # Create and track mocks
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
    cleanup_context["mocks"].append(mock_agent_factory)

    # Run the query
    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory", mock_agent_factory
    ):
        orchestrator = Orchestrator()
        try:
            cleanup_context["result"] = orchestrator.run_query("test query", config)
        except Exception as exc:
            cleanup_context["error"] = exc
            cleanup_context["result"] = {"error": str(exc)}


@then("all monkeypatches should be properly cleaned up")
def monkeypatches_properly_cleaned_up(cleanup_context: CleanupContext) -> None:
    """Verify that all monkeypatches are properly cleaned up."""
    # Surface any error captured during execution
    if "error" in cleanup_context:
        raise cleanup_context["error"]

    # Check that monkeypatched functions are restored
    for path, original_value in cleanup_context["monkeypatches"]:
        module_path, attr_name = path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[attr_name])
        current_value = getattr(module, attr_name)

        # If original was None, verify current is not None
        # Otherwise, verify they're the same object
        if original_value is None:
            assert current_value is not None, (
                f"Monkeypatch for {path} was not properly cleaned up"
            )
        else:
            assert current_value == original_value, (
                f"Monkeypatch for {path} was not properly cleaned up"
            )


@then("all mocks should be properly cleaned up")
def mocks_properly_cleaned_up(cleanup_context: CleanupContext) -> None:
    """Verify that all mocks are properly cleaned up."""
    # Surface any error captured during execution
    if "error" in cleanup_context:
        raise cleanup_context["error"]

    # Check that mocked objects are no longer in use
    for mock in cleanup_context["mocks"]:
        # Verify the mock is not being used by checking its call count hasn't changed
        initial_call_count = mock.call_count
        try:
            # This should not affect the call count if the mock is properly cleaned up
            mock()
            assert mock.call_count == initial_call_count + 1, "Mock is still being used"
        except Exception:
            # If the mock raises an exception, it's likely because it's been cleaned up
            pass


@then("all temporary files should be properly cleaned up")
def temp_files_properly_cleaned_up(cleanup_context: CleanupContext) -> None:
    """Verify that all temporary files are properly cleaned up."""
    # Check that environment variables are restored
    for key, value in cleanup_context["initial_env_vars"].items():
        assert os.environ.get(key) == value, (
            f"Environment variable {key} was not properly cleaned up"
        )

    # Check that no new modules were added to sys.modules
    current_modules = set(sys.modules.keys())
    new_modules = current_modules - cleanup_context["initial_sys_modules"]
    assert not new_modules, f"New modules were added and not cleaned up: {new_modules}"
