from types import MethodType

from autoresearch import mcp_interface
from autoresearch.config.models import ConfigModel


def _mock_load_config():
    return ConfigModel()


def test_client_server_roundtrip(monkeypatch, mock_run_query):
    monkeypatch.setattr(mcp_interface._config_loader, "load_config", _mock_load_config)

    server = mcp_interface.create_server()
    monkeypatch.setattr(
        server.orchestrator,
        "run_query",
        MethodType(mock_run_query, server.orchestrator),
    )

    result = mcp_interface.query("hello", transport=server)

    assert result["answer"] == "ok"
