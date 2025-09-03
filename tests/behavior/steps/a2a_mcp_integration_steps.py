"""Step definitions for A2A MCP integration scenarios."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastmcp import Client, FastMCP
from pytest_bdd import given, scenario, then, when, parsers

from autoresearch import mcp_interface

pytest_plugins = ["tests.behavior.steps.common_steps"]

# Apply common markers to all scenarios in this module.
pytestmark = [pytest.mark.a2a_mcp, pytest.mark.requires_distributed]


@pytest.fixture
def mock_server() -> FastMCP:
    """Provide a mock MCP server."""
    server = FastMCP("Mock")

    @server.tool
    async def research(query: str) -> dict:
        return {"answer": "42"}

    yield server
    server.tools.clear()


@given("a mock MCP server is available", target_fixture="server")
def given_server(mock_server: FastMCP) -> FastMCP:
    """Expose the mock server to scenarios."""
    return mock_server


@when("I perform an A2A MCP handshake")
def perform_a2a_mcp_handshake(server: FastMCP, bdd_context: dict) -> None:
    """Execute a handshake through the MCP interface."""
    response = mcp_interface.query("hello", transport=server)
    bdd_context["response"] = response


@when("the A2A MCP handshake times out")
def handshake_times_out(server: FastMCP, bdd_context: dict) -> None:
    """Simulate a timeout during handshake."""
    with patch(
        "autoresearch.mcp_interface.Client.call_tool",
        side_effect=TimeoutError("timeout"),
    ):
        with pytest.raises(TimeoutError) as exc:
            mcp_interface.query("hello", transport=server)
        bdd_context["error"] = str(exc.value)


@when("the A2A MCP handshake fails once and then succeeds")
def handshake_recovers(server: FastMCP, bdd_context: dict) -> None:
    """Force a transient failure followed by success."""

    class FlakyClient(Client):
        failed = False

        def __init__(self, target):  # pragma: no cover - simple init
            super().__init__(target)

        async def __aenter__(self):  # pragma: no cover
            return self

        async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover
            pass

        async def call_tool(self, name, params):
            if not FlakyClient.failed:
                FlakyClient.failed = True
                raise ConnectionError("temporary failure")
            if hasattr(self.target, "call_tool"):
                return await self.target.call_tool(name, params)
            return {}

    with patch("autoresearch.mcp_interface.Client", FlakyClient):
        with pytest.raises(ConnectionError):
            mcp_interface.query("hello", transport=server)
        response = mcp_interface.query("hello", transport=server)
    bdd_context["response"] = response


@then(parsers.parse('the handshake result should be "{answer}"'))
def check_handshake_result(bdd_context: dict, answer: str) -> None:
    """Validate the handshake response content."""
    assert bdd_context["response"]["answer"] == answer


@then("the A2A interface should report a timeout")
def check_timeout(bdd_context: dict) -> None:
    """Confirm that a timeout error was surfaced."""
    assert "timeout" in bdd_context["error"].lower()


@scenario("../features/a2a_mcp_integration.feature", "Successful A2A MCP handshake")
def test_a2a_mcp_success() -> None:
    """Scenario: happy-path handshake."""
    pass


@scenario("../features/a2a_mcp_integration.feature", "MCP handshake timeout handling")
def test_a2a_mcp_timeout() -> None:
    """Scenario: handshake timeout is handled gracefully."""
    pass


@pytest.mark.error_recovery
@scenario("../features/a2a_mcp_integration.feature", "Error recovery after handshake failure")
def test_a2a_mcp_recovery() -> None:
    """Scenario: handshake recovers after transient failure."""
    pass
