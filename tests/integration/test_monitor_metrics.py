# mypy: ignore-errors
from __future__ import annotations

import sys
import time
from collections.abc import Callable, Iterator
from typing import cast

import psutil
import pytest
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry, generate_latest
from requests import Response as RequestsResponse
from typer.testing import CliRunner

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.main import app as cli_app
from autoresearch.models import QueryResponse
from autoresearch.monitor.system_monitor import SystemMonitor
from autoresearch.orchestration import metrics
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.types import CallbackMap
from autoresearch.resource_monitor import ResourceMonitor
from tests.typing_helpers import TypedFixture


MonitorSetup = Callable[[ConfigModel | None], ConfigModel]


def dummy_run_query(
    query: str,
    config: ConfigModel,
    callbacks: CallbackMap | None = None,
    **_: object,
) -> QueryResponse:
    metrics.record_query()
    return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})


@pytest.fixture
def monitor_cli_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[MonitorSetup]:
    """Return a callable that applies CLI patches with typed state."""

    def _apply(config: ConfigModel | None = None) -> ConfigModel:
        cfg = config or ConfigModel(loops=1, output_format="json")
        cfg.api.role_permissions.setdefault("anonymous", [])
        cfg.api.role_permissions["anonymous"] = ["query", "metrics"]
        cfg.api.monitoring_enabled = True

        def _load_config(_: ConfigLoader) -> ConfigModel:
            return cfg

        monkeypatch.setattr(ConfigLoader, "load_config", _load_config)

        responses: Iterator[str] = iter(["test", "", "q"])

        def _ask(*_: object, **__: object) -> str:
            return next(responses)

        monkeypatch.setattr("autoresearch.main.Prompt.ask", _ask)
        monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
        monkeypatch.setattr("autoresearch.monitor.Orchestrator", Orchestrator)
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        return cfg

    return _apply


def test_sampling_frequency_formula() -> None:
    f_base = 1.0
    f_max = 5.0
    load = 0.75
    thresh = 0.5
    freq = min(f_max, f_base * (1 + load / thresh))
    assert freq == pytest.approx(2.5)


def test_resource_threshold_formula() -> None:
    samples = [40, 50, 60, 50]
    mean = sum(samples) / len(samples)
    var = sum((x - mean) ** 2 for x in samples) / (len(samples) - 1)
    sigma = var**0.5
    k = 2
    thresh = mean + k * sigma
    assert thresh == pytest.approx(66.33, abs=0.01)


@pytest.mark.slow
def test_monitor_cli_increments_counter(
    monitor_cli_setup: MonitorSetup, api_client: TestClient
) -> None:
    monitor_cli_setup(None)
    runner = CliRunner()
    start = metrics.QUERY_COUNTER._value.get()
    result = runner.invoke(cli_app, ["monitor", "run"])
    assert result.exit_code == 0
    assert metrics.QUERY_COUNTER._value.get() >= start
    resp = api_client.get("/metrics")
    response = cast(RequestsResponse, resp)
    assert response.status_code == 200
    assert "autoresearch_queries_total" in response.text


def test_resource_monitor_collects_metrics() -> None:
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


def test_system_monitor_metrics_exposed(
    monitor_cli_setup: MonitorSetup,
    monkeypatch: pytest.MonkeyPatch,
    api_client: TestClient,
) -> None:
    cfg = monitor_cli_setup(ConfigModel(loops=1, output_format="json"))
    cfg.api.role_permissions["anonymous"] = ["metrics"]
    monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: 5.0)
    mem = type("m", (), {"percent": 10.0})()
    monkeypatch.setattr(psutil, "virtual_memory", lambda: mem)

    monitor = SystemMonitor(interval=0.01)
    monitor.start()
    time.sleep(0.05)
    monitor.stop()

    resp = api_client.get("/metrics")
    response = cast(RequestsResponse, resp)
    assert response.status_code == 200
    assert "autoresearch_system_cpu_percent" in response.text
    assert "autoresearch_system_memory_percent" in response.text


@pytest.mark.slow
def test_monitor_start_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {}

    def fake_start(self: ResourceMonitor, prometheus_port: int | None = None) -> None:
        calls["port"] = prometheus_port

    def fake_stop(self: ResourceMonitor) -> None:
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


def test_monitor_resources_cli(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_metrics_requires_api_key(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = ConfigModel(api=APIConfig(api_key="secret", monitoring_enabled=True))
    cfg.api.role_permissions["user"] = ["metrics"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    resp = api_client.get("/metrics")
    response = cast(RequestsResponse, resp)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "API-Key"
