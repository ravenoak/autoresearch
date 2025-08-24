import asyncio

from autoresearch.api.utils import generate_bearer_token
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel


def _setup(monkeypatch):
    cfg = ConfigModel(api=APIConfig())
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


def test_invalid_bearer_token(monkeypatch, api_client):
    """Invalid bearer token should return 401."""
    cfg = _setup(monkeypatch)
    cfg.api.bearer_token = generate_bearer_token()
    resp = api_client.post("/query", json={"query": "q"}, headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


def test_missing_bearer_token(monkeypatch, api_client):
    """Requests without a token are rejected."""
    cfg = _setup(monkeypatch)
    cfg.api.bearer_token = generate_bearer_token()
    resp = api_client.post("/query", json={"query": "q"})
    assert resp.status_code == 401


def test_permission_denied(monkeypatch, api_client):
    """API key lacking permission results in 403."""
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"u": "user"}
    cfg.api.role_permissions = {"user": ["query"]}
    resp = api_client.get("/metrics", headers={"X-API-Key": "u"})
    assert resp.status_code == 403


def test_docs_protected(monkeypatch, api_client):
    """Documentation endpoints require authentication when configured."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"

    unauth = api_client.get("/docs")
    assert unauth.status_code == 401

    ok = api_client.get("/docs", headers={"X-API-Key": "secret"})
    assert ok.status_code == 200

    openapi = api_client.get("/openapi.json", headers={"X-API-Key": "secret"})
    assert openapi.status_code == 200


def test_invalid_key_and_token(monkeypatch, api_client):
    """Both credentials invalid results in 401."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    cfg.api.bearer_token = generate_bearer_token()
    resp = api_client.post(
        "/query",
        json={"query": "q"},
        headers={"X-API-Key": "wrong", "Authorization": "Bearer bad"},
    )
    assert resp.status_code == 401


def test_query_status_permission_denied(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"u": "user"}
    cfg.api.role_permissions = {"user": []}
    api_client.app.state.async_tasks["id"] = asyncio.Future()
    resp = api_client.get("/query/id", headers={"X-API-Key": "u"})
    assert resp.status_code == 403


def test_cancel_query_permission_denied(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"u": "user"}
    cfg.api.role_permissions = {"user": []}
    api_client.app.state.async_tasks["id"] = asyncio.Future()
    resp = api_client.delete("/query/id", headers={"X-API-Key": "u"})
    assert resp.status_code == 403
