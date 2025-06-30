from typer.testing import CliRunner
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry, generate_latest
import time

from autoresearch.main import app as cli_app
from autoresearch.api import app as api_app
from autoresearch.config import ConfigLoader, ConfigModel
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
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    responses = iter(["test", ""])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)


def test_monitor_cli_increments_counter(monkeypatch):
    setup_patches(monkeypatch)
    runner = CliRunner()
    start = metrics.QUERY_COUNTER._value.get()
    result = runner.invoke(cli_app, ["monitor", "run"])
    assert result.exit_code == 0
    assert metrics.QUERY_COUNTER._value.get() == start + 1
    client = TestClient(api_app)
    resp = client.get("/metrics")
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


def test_system_monitor_metrics_exposed(monkeypatch):
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

    client = TestClient(api_app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "autoresearch_system_cpu_percent" in resp.text
    assert "autoresearch_system_memory_percent" in resp.text


def test_monitor_start_cli(monkeypatch):
    calls = {}

    def fake_start(self, prometheus_port=None):
        calls["port"] = prometheus_port

    def fake_stop(self):
        calls["stop"] = True

    monkeypatch.setattr(ResourceMonitor, "start", fake_start)
    monkeypatch.setattr(ResourceMonitor, "stop", fake_stop)
    monkeypatch.setattr("autoresearch.monitor.SystemMonitor.start", lambda self: calls.setdefault("sys_start", True))
    monkeypatch.setattr("autoresearch.monitor.SystemMonitor.stop", lambda self: calls.setdefault("sys_stop", True))
    monkeypatch.setattr("autoresearch.monitor.time.sleep", lambda x: (_ for _ in ()).throw(KeyboardInterrupt()))

    runner = CliRunner()
    result = runner.invoke(cli_app, ["monitor", "start", "--prometheus", "--port", "9999", "--interval", "0.1"])
    assert result.exit_code == 0
    assert calls["port"] == 9999
    assert calls["stop"]
    assert calls["sys_start"]
    assert calls["sys_stop"]
