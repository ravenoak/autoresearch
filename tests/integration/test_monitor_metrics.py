from typer.testing import CliRunner
from fastapi.testclient import TestClient
from autoresearch.main import app as cli_app
from autoresearch.api import app as api_app
from autoresearch.config import ConfigLoader, ConfigModel
from autoresearch.orchestration import metrics
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


def dummy_run_query(query, config, callbacks=None, **kwargs):
    metrics.record_query()
    return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})


def setup_patches(monkeypatch):
    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: ConfigModel(loops=1, output_format="json"),
    )
    responses = iter(["test", ""])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)


def test_monitor_cli_increments_counter(monkeypatch):
    setup_patches(monkeypatch)
    runner = CliRunner()
    start = metrics.QUERY_COUNTER._value.get()
    result = runner.invoke(cli_app, ["monitor"])
    assert result.exit_code == 0
    assert metrics.QUERY_COUNTER._value.get() == start + 1
    client = TestClient(api_app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "autoresearch_queries_total" in resp.text
