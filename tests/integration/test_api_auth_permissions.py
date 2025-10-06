# mypy: ignore-errors
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


def _setup(monkeypatch: pytest.MonkeyPatch) -> ConfigModel:
    cfg = ConfigModel(api=APIConfig())
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )
    return cfg


def test_permission_success(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"adm": "admin"}
    cfg.api.role_permissions = {"admin": ["metrics"]}
    resp = api_client.get("/metrics", headers={"X-API-Key": "adm"})
    assert resp.status_code == 200


def test_permission_forbidden(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"usr": "user"}
    cfg.api.role_permissions = {"user": []}
    resp = api_client.get("/metrics", headers={"X-API-Key": "usr"})
    assert resp.status_code == 403


def test_permission_unauthenticated(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    resp = api_client.get("/metrics")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing API key"


def test_permission_invalid_key(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"adm": "admin"}
    cfg.api.role_permissions = {"admin": ["metrics"]}
    resp = api_client.get("/metrics", headers={"X-API-Key": "bad"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid API key"
