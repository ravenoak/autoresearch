import pytest
from fastmcp import Client, FastMCP

from autoresearch import mcp_interface

pytestmark = [pytest.mark.unit, pytest.mark.a2a_mcp, pytest.mark.requires_distributed]


@pytest.fixture
def server() -> FastMCP:
    server = FastMCP("Mock")

    @server.tool
    async def research(query: str) -> dict:
        return {"answer": "42"}

    yield server
    server.tools.clear()


def test_handshake_success(server: FastMCP) -> None:
    result = mcp_interface.query("hello", transport=server)
    assert result["answer"] == "42"


def test_handshake_timeout(server: FastMCP, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _timeout(self, name, params):
        raise TimeoutError("timeout")

    monkeypatch.setattr("autoresearch.mcp_interface.Client.call_tool", _timeout)

    with pytest.raises(TimeoutError):
        mcp_interface.query("hello", transport=server)


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

    with pytest.raises(ConnectionError):
        mcp_interface.query("hello", transport=server)

    result = mcp_interface.query("hello", transport=server)
    assert result["answer"] == "42"
