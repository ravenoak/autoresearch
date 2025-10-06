from __future__ import annotations

import contextlib
import types
from typing import Any, NoReturn

import pytest
from fastapi.testclient import TestClient

from autoresearch.api import app
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator
from scripts.simulate_api_auth_errors import simulate


def _setup(monkeypatch: pytest.MonkeyPatch) -> ConfigModel:
    cfg: ConfigModel = ConfigModel.model_construct(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr("autoresearch.api.routing.get_config", lambda: cfg)
    dummy_loader = types.SimpleNamespace(
        config=cfg, watching=lambda *a, **k: contextlib.nullcontext()
    )
    monkeypatch.setattr("autoresearch.api.config_loader", dummy_loader)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader.reset_instance()
    monkeypatch.setattr(
        "autoresearch.api.webhooks.notify_webhook",
        lambda u, r, timeout=5: None,
    )
    return cfg


def test_query_endpoint_runtime_error(
    monkeypatch: pytest.MonkeyPatch, orchestrator: Orchestrator
) -> None:
    _setup(monkeypatch)

    orch: Orchestrator = orchestrator

    def raise_error(
        q: str, c: ConfigModel, callbacks: Any | None = None
    ) -> NoReturn:
        raise RuntimeError("fail")

    monkeypatch.setattr(orch, "run_query", raise_error)
    monkeypatch.setattr("autoresearch.api.routing.create_orchestrator", lambda: orch)
    client: TestClient = TestClient(app)
    resp = client.post("/query", json={"query": "q"})
    assert resp.status_code == 200
    data: dict[str, Any] = resp.json()
    assert data["answer"].startswith("Error: fail")
    assert data["metrics"]["error"] == "fail"


def test_query_endpoint_invalid_response(
    monkeypatch: pytest.MonkeyPatch, orchestrator: Orchestrator
) -> None:
    _setup(monkeypatch)
    orch: Orchestrator = orchestrator
    monkeypatch.setattr(
        orch,
        "run_query",
        lambda q, c, callbacks=None: {"foo": "bar"},
    )
    monkeypatch.setattr("autoresearch.api.routing.create_orchestrator", lambda: orch)
    client: TestClient = TestClient(app)
    resp = client.post("/query", json={"query": "q"})
    assert resp.status_code == 200
    data: dict[str, Any] = resp.json()
    assert data["answer"] == "Error: Invalid response format"
    assert data["metrics"]["error"] == "Invalid response format"


def test_simulate_api_auth_error_rates() -> None:
    counts = simulate(1000, 0.2, 0.3, 0.1, seed=0)
    assert counts[400] == 201
    assert counts[401] == 307
    assert counts[429] == 89
    assert sum(counts.values()) == 1000
