# mypy: ignore-errors
from __future__ import annotations

from collections.abc import Iterator
from types import TracebackType
from typing import Any, cast
from unittest.mock import patch

import pytest
from fastmcp import Client, FastMCP
from pytest_bdd import given, scenario, then, when

import tests.stubs.fastmcp  # noqa: F401
from autoresearch import mcp_interface

from tests.behavior.context import BehaviorContext, get_required, set_value
from tests.behavior.utils import PayloadDict, as_payload

pytest_plugins = ["tests.behavior.steps.common_steps"]


@pytest.fixture
def mock_server() -> Iterator[FastMCP]:
    """Provide a mock MCP server for scenarios and ensure cleanup."""
    server = FastMCP("Mock")

    @server.tool
    async def research(query: str) -> PayloadDict:
        if query == "bad":
            raise ValueError("malformed request")
        return as_payload({"answer": "42"})

    yield server

    server.tools.clear()


@given("a mock MCP server is available", target_fixture="server")
def given_server(mock_server: FastMCP) -> FastMCP:
    return mock_server


@when('I send a MCP query "{query}"')
def send_mcp_query(
    server: FastMCP, bdd_context: BehaviorContext, query: str
) -> None:
    response = mcp_interface.query(query, transport=server)
    set_value(bdd_context, "response", response)


@then('I should receive a MCP response with answer "{answer}"')
def check_mcp_response(bdd_context: BehaviorContext, answer: str) -> None:
    response = get_required(bdd_context, "response")
    assert response["answer"] == answer


@when("I send a malformed MCP request")
def send_malformed_request(server: FastMCP, bdd_context: BehaviorContext) -> None:
    with pytest.raises(Exception) as exc:
        mcp_interface.query("bad", transport=server)
    set_value(bdd_context, "error", str(exc.value))


@then("the MCP client should receive an error response")
def check_malformed_error(bdd_context: BehaviorContext) -> None:
    error = get_required(bdd_context, "error", str)
    assert "malformed" in error.lower()


@when("a connection interruption occurs and the client retries")
def retry_after_connection_failure(
    server: FastMCP, bdd_context: BehaviorContext
) -> None:
    class FlakyClient(Client):
        def __init__(self, target: Any) -> None:  # pragma: no cover - simple init
            super().__init__(target)
            self.failed = False

        async def __aenter__(self) -> Client:  # pragma: no cover - context manager
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            return None

        async def call_tool(self, name: str, params: Any) -> PayloadDict:
            if not self.failed:
                self.failed = True
                raise ConnectionError("temporary outage")
            if hasattr(self.target, "call_tool"):
                result = await self.target.call_tool(name, params)
                return cast(PayloadDict, result)
            return as_payload({})

    with patch("autoresearch.mcp_interface.Client", FlakyClient):
        with pytest.raises(ConnectionError):
            mcp_interface.query("hello", transport=server)
        result = mcp_interface.query("hello", transport=server)
    set_value(bdd_context, "response", result)


@then('the client should eventually receive a MCP response with answer "{answer}"')
def check_recovered_response(
    bdd_context: BehaviorContext, answer: str
) -> None:
    response = get_required(bdd_context, "response")
    assert response["answer"] == answer


@scenario("../features/mcp_interface.feature", "Successful query exchange")
def test_mcp_success() -> None:
    pass


@scenario("../features/mcp_interface.feature", "Malformed request handling")
def test_mcp_malformed() -> None:
    pass


@scenario("../features/mcp_interface.feature", "Connection failure recovery")
def test_mcp_recovery() -> None:
    pass
