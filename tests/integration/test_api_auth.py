import asyncio

from fastapi import Request
from fastapi.responses import JSONResponse

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
    assert resp.json()["detail"] == "Invalid token"


def test_role_assignments(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"adm": "admin"}
    token = generate_bearer_token()
    cfg.api.bearer_token = token

    @api_client.app.get("/whoami")
    async def whoami(request: Request):
        return JSONResponse({"role": request.state.role})

    resp_key = api_client.get("/whoami", headers={"X-API-Key": "adm"})
    assert resp_key.status_code == 200
    assert resp_key.json() == {"role": "admin"}

    resp_token = api_client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert resp_token.status_code == 200
    assert resp_token.json() == {"role": "user"}

    resp_bad = api_client.get("/whoami", headers={"X-API-Key": "bad"})
    assert resp_bad.status_code == 401
    assert resp_bad.json()["detail"] == "Invalid API key"

    resp_missing = api_client.get("/whoami")
    assert resp_missing.status_code == 401
    assert resp_missing.json()["detail"] == "Missing API key or token"


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
    assert missing.json()["detail"] == "Missing API key"


def test_invalid_api_key(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"good": "user"}

    bad = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "bad"})
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid API key"


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
    assert missing.json()["detail"] == "Missing API key or token"


def test_invalid_api_key_with_valid_token(monkeypatch, api_client):
    """Invalid API key causes rejection even when token is valid."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    token = generate_bearer_token()
    cfg.api.bearer_token = token
    resp = api_client.post(
        "/query",
        json={"query": "q"},
        headers={"X-API-Key": "bad", "Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid API key"


def test_invalid_token_with_valid_api_key(monkeypatch, api_client):
    """Invalid bearer token is rejected even with a valid API key."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    cfg.api.bearer_token = generate_bearer_token()
    resp = api_client.post(
        "/query",
        json={"query": "q"},
        headers={"X-API-Key": "secret", "Authorization": "Bearer bad"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"


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
    assert resp.json()["detail"] == "Invalid token"


def test_missing_bearer_token(monkeypatch, api_client):
    """Requests without a token are rejected."""
    cfg = _setup(monkeypatch)
    cfg.api.bearer_token = generate_bearer_token()
    resp = api_client.post("/query", json={"query": "q"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing token"


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
