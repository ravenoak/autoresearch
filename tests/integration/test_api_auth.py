import asyncio

from autoresearch.api.utils import generate_bearer_token
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
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )
    return cfg


def test_http_bearer_token(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    token = generate_bearer_token()
    cfg.api.bearer_token = token

    resp = api_client.post(
        "/query", json={"query": "q"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    resp = api_client.post("/query", json={"query": "q"}, headers={"Authorization": "Bearer bad"})
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

    denied = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "usr"})
    assert denied.status_code == 403


def test_single_api_key(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"

    ok = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "secret"})
    assert ok.status_code == 200

    missing = api_client.post("/query", json={"query": "q"})
    assert missing.status_code == 401


def test_invalid_api_key(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"good": "user"}

    bad = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "bad"})
    assert bad.status_code == 401


def test_api_key_or_token(monkeypatch, api_client):
    """Either a valid API key or bearer token authenticates the request."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    token = generate_bearer_token()
    cfg.api.bearer_token = token

    ok_key = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "secret"})
    assert ok_key.status_code == 200

    ok_token = api_client.post(
        "/query", json={"query": "q"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert ok_token.status_code == 200

    missing = api_client.post("/query", json={"query": "q"})
    assert missing.status_code == 401


def test_token_overrides_invalid_api_key(monkeypatch, api_client):
    """Valid token bypasses an incorrect API key header."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    token = generate_bearer_token()
    cfg.api.bearer_token = token
    resp = api_client.post(
        "/query",
        json={"query": "q"},
        headers={"X-API-Key": "bad", "Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_api_key_overrides_invalid_token(monkeypatch, api_client):
    """Valid API key is accepted even when token is incorrect."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    cfg.api.bearer_token = generate_bearer_token()
    resp = api_client.post(
        "/query",
        json={"query": "q"},
        headers={"X-API-Key": "secret", "Authorization": "Bearer bad"},
    )
    assert resp.status_code == 200


def test_query_status_and_cancel(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"adm": "admin"}
    cfg.api.role_permissions = {"admin": ["query"]}

    loop = asyncio.new_event_loop()
    future = loop.create_future()
    future.set_result(QueryResponse(answer="ok", citations=[], reasoning=[], metrics={}))
    api_client.app.state.async_tasks["abc"] = future

    status = api_client.get("/query/abc", headers={"X-API-Key": "adm"})
    assert status.status_code == 200

    future2 = loop.create_future()
    api_client.app.state.async_tasks["def"] = future2
    cancel = api_client.delete("/query/def", headers={"X-API-Key": "adm"})
    assert cancel.status_code == 200


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
    api_client.app.state.async_tasks["id"] = asyncio.new_event_loop().create_future()
    resp = api_client.get("/query/id", headers={"X-API-Key": "u"})
    assert resp.status_code == 403


def test_cancel_query_permission_denied(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"u": "user"}
    cfg.api.role_permissions = {"user": []}
    api_client.app.state.async_tasks["id"] = asyncio.new_event_loop().create_future()
    resp = api_client.delete("/query/id", headers={"X-API-Key": "u"})
    assert resp.status_code == 403
