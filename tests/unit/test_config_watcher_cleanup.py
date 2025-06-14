import threading
from typer.testing import CliRunner
from fastapi.testclient import TestClient

from autoresearch.main import app as cli_app
from autoresearch.api import app as api_app
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


def _mock_run_query(query, config):
    return QueryResponse(answer="a", citations=[], reasoning=[], metrics={})


def test_cli_watcher_cleanup(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query)
    result = runner.invoke(cli_app, ["search", "q"])
    assert result.exit_code == 0
    assert not any(
        t.name == "ConfigWatcher" and t.is_alive()
        for t in threading.enumerate()
    )


def test_api_watcher_cleanup(monkeypatch):
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query)
    with TestClient(api_app) as client:
        resp = client.post("/query", json={"query": "q"})
        assert resp.status_code == 200
    assert not any(
        t.name == "ConfigWatcher" and t.is_alive()
        for t in threading.enumerate()
    )
