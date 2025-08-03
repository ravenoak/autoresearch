import threading
import time
from typer.testing import CliRunner
from fastapi.testclient import TestClient

from autoresearch.main import app as cli_app
from autoresearch.api import app as api_app
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


def _mock_run_query(query, config, *args, **kwargs):
    return QueryResponse(answer="a", citations=[], reasoning=[], metrics={})


def _mock_run_query_error(query, config, *args, **kwargs):
    raise RuntimeError("boom")


def test_cli_watcher_cleanup(monkeypatch):
    initial = sum(
        1 for t in threading.enumerate() if t.name == "ConfigWatcher" and t.is_alive()
    )
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query)
    result = runner.invoke(cli_app, ["search", "q"])
    assert result.exit_code == 0
    for _ in range(10):
        if (
            sum(
                1
                for t in threading.enumerate()
                if t.name == "ConfigWatcher" and t.is_alive()
            )
            <= initial
        ):
            break
        time.sleep(0.1)
    assert (
        sum(
            1 for t in threading.enumerate() if t.name == "ConfigWatcher" and t.is_alive()
        )
        <= initial
    )


def test_api_watcher_cleanup(monkeypatch):
    initial = sum(
        1 for t in threading.enumerate() if t.name == "ConfigWatcher" and t.is_alive()
    )
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query)
    with TestClient(api_app) as client:
        resp = client.post("/query", json={"query": "q"})
        assert resp.status_code == 200
    for _ in range(10):
        if (
            sum(
                1
                for t in threading.enumerate()
                if t.name == "ConfigWatcher" and t.is_alive()
            )
            <= initial
        ):
            break
        time.sleep(0.1)
    assert (
        sum(
            1 for t in threading.enumerate() if t.name == "ConfigWatcher" and t.is_alive()
        )
        <= initial
    )


def test_cli_watcher_cleanup_error(monkeypatch):
    initial = sum(
        1 for t in threading.enumerate() if t.name == "ConfigWatcher" and t.is_alive()
    )
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query_error)
    runner.invoke(cli_app, ["search", "q"])
    for _ in range(10):
        if (
            sum(
                1
                for t in threading.enumerate()
                if t.name == "ConfigWatcher" and t.is_alive()
            )
            <= initial
        ):
            break
        time.sleep(0.1)
    assert (
        sum(
            1 for t in threading.enumerate() if t.name == "ConfigWatcher" and t.is_alive()
        )
        <= initial
    )


def test_api_watcher_cleanup_error(monkeypatch):
    initial = sum(
        1 for t in threading.enumerate() if t.name == "ConfigWatcher" and t.is_alive()
    )
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query_error)
    with TestClient(api_app) as client:
        client.post("/query", json={"query": "q"})
    for _ in range(10):
        if (
            sum(
                1
                for t in threading.enumerate()
                if t.name == "ConfigWatcher" and t.is_alive()
            )
            <= initial
        ):
            break
        time.sleep(0.1)
    assert (
        sum(
            1 for t in threading.enumerate() if t.name == "ConfigWatcher" and t.is_alive()
        )
        <= initial
    )
