from types import MethodType
from typing import Any

import pytest
from fastmcp import Client, FastMCP

from autoresearch import mcp_interface
from autoresearch.api.models import QueryResponseV1
from autoresearch.errors import AgentError

pytestmark = [pytest.mark.unit, pytest.mark.a2a_mcp, pytest.mark.requires_distributed]


@pytest.fixture
def server() -> FastMCP:
    try:
        server = FastMCP("Mock")
    except TypeError:
        server = FastMCP()

    @server.tool
    async def research(query: str, version: str = "1", **overrides: Any) -> dict:
        _ = overrides  # Exercise kwargs for coverage while staying simple.
        response = QueryResponseV1(
            query=query,
            answer="42",
            citations=[],
            reasoning=["Socratic check: Did the handshake complete successfully?"],
            metrics={"cycles_completed": 1},
            react_traces=[],
        )
        response.version = version
        return response.model_dump(mode="json")

    yield server
    server.tools.clear()


def test_handshake_success(server: FastMCP) -> None:
    result = mcp_interface.query("hello", transport=server)
    assert result["answer"] == "42", (
        "Socratic check: Did the MCP handshake deliver orchestrator output?"
    )
    assert any("Socratic check" in step for step in result["reasoning"]), (
        "Socratic check: Did the response capture reflective guidance?"
    )
    assert result["metrics"]["cycles_completed"] == 1, (
        "Socratic check: Are success metrics surfaced for auditing?"
    )


def test_handshake_timeout(server: FastMCP, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _timeout(self, name, params):
        raise TimeoutError("timeout")

    monkeypatch.setattr("autoresearch.mcp_interface.Client.call_tool", _timeout)

    with pytest.raises(TimeoutError) as exc_info:
        mcp_interface.query("hello", transport=server)

    assert "timeout" in str(exc_info.value).lower(), (
        "Socratic check: Did the client propagate timeout diagnostics?"
    )


def test_handshake_recovery(server: FastMCP, monkeypatch: pytest.MonkeyPatch) -> None:
    class FlakyClient(Client):
        failed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def call_tool(self, name, params):
            if not FlakyClient.failed:
                FlakyClient.failed = True
                raise ConnectionError("temporary failure")
            if hasattr(self.target, "call_tool"):
                return await self.target.call_tool(name, params)
            return {}

    monkeypatch.setattr("autoresearch.mcp_interface.Client", FlakyClient)

    with pytest.raises(ConnectionError) as exc_info:
        mcp_interface.query("hello", transport=server)

    assert "temporary failure" in str(exc_info.value).lower(), (
        "Socratic check: Did the retry logic surface the transient failure?"
    )

    result = mcp_interface.query("hello", transport=server)
    assert result["answer"] == "42", (
        "Socratic check: Did the client recover after the transient failure?"
    )


def test_handshake_server_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    server = mcp_interface.create_server()

    def fail(self, _query: str, _config: object, **_kwargs: Any) -> QueryResponseV1:
        raise AgentError("broken", context={"agent": "Handshake"})

    monkeypatch.setattr(
        server.orchestrator,
        "run_query",
        MethodType(fail, server.orchestrator),
    )

    result = mcp_interface.query("hello", transport=server)

    assert result["answer"].startswith("Error:"), (
        "Socratic check: Did server failures bubble up as structured errors?"
    )
    assert any(step.startswith("Socratic check") for step in result["reasoning"]), (
        "Socratic check: Are follow-up prompts included for diagnosis?"
    )
    assert result["metrics"].get("error"), (
        "Socratic check: Are error metrics captured for telemetry?"
    )
