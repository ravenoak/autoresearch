"""Step definitions for A2A MCP integration scenarios."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastmcp import Client, FastMCP
from pytest_bdd import given, scenario, then, when

from autoresearch import mcp_interface

pytest_plugins = ["tests.behavior.steps.common_steps"]


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
    return mock_server


@when('I send an A2A MCP query "{query}"')
def send_a2a_mcp_query(server: FastMCP, bdd_context: dict, query: str) -> None:
    response = mcp_interface.query(query, transport=server)
    bdd_context["response"] = response


@when("the MCP query times out")
def mcp_query_times_out(server: FastMCP, bdd_context: dict) -> None:
    with patch(
        "autoresearch.mcp_interface.Client.call_tool",
        side_effect=TimeoutError("timeout"),
    ):
        with pytest.raises(TimeoutError) as exc:
            mcp_interface.query("hello", transport=server)
        bdd_context["error"] = str(exc.value)


@when("the MCP query fails once and then succeeds")
def mcp_query_recovers(server: FastMCP, bdd_context: dict) -> None:
    class FlakyClient(Client):
        def __init__(self, target):  # pragma: no cover - simple init
            super().__init__(target)
            self.failed = False

        async def __aenter__(self):  # pragma: no cover - context manager
            return self

        async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover - context
            pass

        async def call_tool(self, name, params):
            if not self.failed:
                self.failed = True
                raise ConnectionError("temporary failure")
            if hasattr(self.target, "call_tool"):
                return await self.target.call_tool(name, params)
            return {}

    with patch("autoresearch.mcp_interface.Client", FlakyClient):
        with pytest.raises(ConnectionError):
            mcp_interface.query("hello", transport=server)
        response = mcp_interface.query("hello", transport=server)
    bdd_context["response"] = response


@then('the MCP answer should be "{answer}"')
def check_mcp_answer(bdd_context: dict, answer: str) -> None:
    assert bdd_context["response"]["answer"] == answer


@then("the A2A interface should report a timeout")
def check_timeout(bdd_context: dict) -> None:
    assert "timeout" in bdd_context["error"].lower()


@pytest.mark.a2a_mcp
@pytest.mark.requires_distributed
@scenario("../features/a2a_mcp_integration.feature", "Successful A2A to MCP query")
def test_a2a_mcp_success() -> None:
    pass


@pytest.mark.a2a_mcp
@pytest.mark.requires_distributed
@scenario("../features/a2a_mcp_integration.feature", "MCP timeout handling")
def test_a2a_mcp_timeout() -> None:
    pass


@pytest.mark.a2a_mcp
@pytest.mark.error_recovery
@pytest.mark.requires_distributed
@scenario("../features/a2a_mcp_integration.feature", "Error recovery after MCP failure")
def test_a2a_mcp_recovery() -> None:
    pass
