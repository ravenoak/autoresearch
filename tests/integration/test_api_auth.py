import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


def _setup(monkeypatch):
    cfg = ConfigModel(api=APIConfig())
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(answer="ok", citations=[], reasoning=[], metrics={}),
    )
    return cfg


def test_http_bearer_token(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.bearer_token = "token"

    resp = api_client.post(
        "/query", json={"query": "q"}, headers={"Authorization": "Bearer token"}
    )
    assert resp.status_code == 200

    resp = api_client.post(
        "/query", json={"query": "q"}, headers={"Authorization": "Bearer bad"}
    )
    assert resp.status_code == 401


def test_rate_limit(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 1

    resp1 = api_client.post("/query", json={"query": "q"})
    assert resp1.status_code == 200
    resp2 = api_client.post("/query", json={"query": "q"})
    assert resp2.status_code == 429
    assert resp2.text == "rate limit exceeded"


def test_rate_limit_configurable(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 2

    assert api_client.post("/query", json={"query": "q"}).status_code == 200
    assert api_client.post("/query", json={"query": "q"}).status_code == 200
    assert api_client.post("/query", json={"query": "q"}).status_code == 429


def test_role_permissions(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"adm": "admin", "usr": "user"}
    cfg.api.role_permissions = {"admin": ["query"], "user": []}

    ok = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "adm"})
    assert ok.status_code == 200

    denied = api_client.post(
        "/query", json={"query": "q"}, headers={"X-API-Key": "usr"}
    )
    assert denied.status_code == 403


def test_single_api_key(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"

    ok = api_client.post(
        "/query", json={"query": "q"}, headers={"X-API-Key": "secret"}
    )
    assert ok.status_code == 200

    missing = api_client.post("/query", json={"query": "q"})
    assert missing.status_code == 401


def test_invalid_api_key(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"good": "user"}

    bad = api_client.post(
        "/query", json={"query": "q"}, headers={"X-API-Key": "bad"}
    )
    assert bad.status_code == 401
