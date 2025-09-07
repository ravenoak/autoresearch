import time

import pytest
from typer.testing import CliRunner
from prometheus_client import CollectorRegistry, generate_latest

from autoresearch.main import app as cli_app
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration import metrics
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse
from autoresearch.resource_monitor import ResourceMonitor
from autoresearch.monitor.system_monitor import SystemMonitor
import psutil


def dummy_run_query(query, config, callbacks=None, **kwargs):
    metrics.record_query()
    return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})


def setup_patches(monkeypatch):
    cfg = ConfigModel(loops=1, output_format="json")
    cfg.api.role_permissions["anonymous"] = ["query", "metrics"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    responses = iter(["test", "", "q"])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    monkeypatch.setattr("autoresearch.monitor.Orchestrator", Orchestrator)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)


@pytest.mark.slow
def test_monitor_cli_increments_counter(monkeypatch, api_client):
    setup_patches(monkeypatch)
    runner = CliRunner()
    start = metrics.QUERY_COUNTER._value.get()
    result = runner.invoke(cli_app, ["monitor", "run"])
    assert result.exit_code == 0
    assert metrics.QUERY_COUNTER._value.get() >= start
    resp = api_client.get("/metrics")
    assert resp.status_code == 200
    assert "autoresearch_queries_total" in resp.text


def test_resource_monitor_collects_metrics():
    registry = CollectorRegistry()
    monitor = ResourceMonitor(interval=0.01, registry=registry)
    monitor.start()
    time.sleep(0.05)
    monitor.stop()
    data = generate_latest(registry).decode()
    assert "autoresearch_cpu_percent" in data
    assert "autoresearch_memory_mb" in data
    assert "autoresearch_gpu_percent" in data
    assert "autoresearch_gpu_memory_mb" in data
    assert "autoresearch_tokens_in_snapshot_total" in data
    assert "autoresearch_tokens_out_snapshot_total" in data
    assert monitor.token_snapshots


def test_system_monitor_metrics_exposed(monkeypatch, api_client):
    setup_patches(monkeypatch)
    cfg = ConfigModel(loops=1, output_format="json")
    cfg.api.role_permissions["anonymous"] = ["metrics"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: 5.0)
    mem = type("m", (), {"percent": 10.0})()
    monkeypatch.setattr(psutil, "virtual_memory", lambda: mem)

    monitor = SystemMonitor(interval=0.01)
    monitor.start()
    time.sleep(0.05)
    monitor.stop()

    resp = api_client.get("/metrics")
    assert resp.status_code == 200
    assert "autoresearch_system_cpu_percent" in resp.text
    assert "autoresearch_system_memory_percent" in resp.text


@pytest.mark.slow
def test_monitor_start_cli(monkeypatch):
    calls = {}

    def fake_start(self, prometheus_port=None):
        calls["port"] = prometheus_port

    def fake_stop(self):
        calls["stop"] = True

    monkeypatch.setattr(ResourceMonitor, "start", fake_start)
    monkeypatch.setattr(ResourceMonitor, "stop", fake_stop)
    monkeypatch.setattr(
        "autoresearch.monitor.SystemMonitor.start",
        lambda self: calls.setdefault("sys_start", True),
    )
    monkeypatch.setattr(
        "autoresearch.monitor.SystemMonitor.stop",
        lambda self: calls.setdefault("sys_stop", True),
    )
    monkeypatch.setattr(
        "autoresearch.monitor.time.sleep",
        lambda x: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        ["monitor", "start", "--prometheus", "--port", "9999", "--interval", "0.1"],
    )
    assert result.exit_code == 0
    assert calls["port"] == 9999
    assert calls["stop"]
    assert calls["sys_start"]
    assert calls["sys_stop"]


def test_monitor_resources_cli(monkeypatch):
    monkeypatch.setattr(
        metrics,
        "_get_system_usage",
        lambda: (10.0, 20.0, 30.0, 40.0),
    )
    runner = CliRunner()
    result = runner.invoke(cli_app, ["monitor", "resources", "--duration", "1"])
    assert result.exit_code == 0
    out = result.stdout
    assert "GPU %" in out
    assert "GPU MB" in out
