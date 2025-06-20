from autoresearch import mcp_interface
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse
from autoresearch.config import ConfigModel


def _mock_run_query(query, config):
    return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})


def _mock_load_config():
    return ConfigModel()


def test_client_server_roundtrip(monkeypatch):
    monkeypatch.setattr(mcp_interface._config_loader, "load_config", _mock_load_config)
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query)

    server = mcp_interface.create_server()

    result = mcp_interface.query("hello", transport=server)

    assert result["answer"] == "ok"
