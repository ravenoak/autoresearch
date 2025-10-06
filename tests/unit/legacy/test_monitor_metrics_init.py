from typer.testing import CliRunner

from autoresearch.main import app as cli_app


def test_monitor_cli_initializes_metrics(monkeypatch):
    called = {"done": False}

    def fake_init() -> None:
        called["done"] = True

    monkeypatch.setattr("autoresearch.monitor.orch_metrics.ensure_counters_initialized", fake_init)
    monkeypatch.setattr("autoresearch.monitor._collect_system_metrics", lambda: {})
    runner = CliRunner()
    result = runner.invoke(cli_app, ["monitor", "metrics"])
    assert result.exit_code == 0
    assert called["done"]
