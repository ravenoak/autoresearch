from fastapi.testclient import TestClient

from autoresearch.api import app as api_app
from autoresearch.config.models import ConfigModel, APIConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


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


def test_http_bearer_token(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.bearer_token = "token"
    client = TestClient(api_app)

    resp = client.post("/query", json={"query": "q"}, headers={"Authorization": "Bearer token"})
    assert resp.status_code == 200

    resp = client.post("/query", json={"query": "q"}, headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 401


def test_rate_limit(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 1
    client = TestClient(api_app)

    resp1 = client.post("/query", json={"query": "q"})
    assert resp1.status_code == 200
    resp2 = client.post("/query", json={"query": "q"})
    assert resp2.status_code == 429
    assert resp2.text == "rate limit exceeded"


def test_rate_limit_configurable(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 2
    client = TestClient(api_app)

    assert client.post("/query", json={"query": "q"}).status_code == 200
    assert client.post("/query", json={"query": "q"}).status_code == 200
    assert client.post("/query", json={"query": "q"}).status_code == 429


def test_role_permissions(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"adm": "admin", "usr": "user"}
    cfg.api.role_permissions = {"admin": ["query"], "user": []}
    client = TestClient(api_app)

    ok = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "adm"})
    assert ok.status_code == 200

    denied = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "usr"})
    assert denied.status_code == 403


def test_single_api_key(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    client = TestClient(api_app)

    ok = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "secret"})
    assert ok.status_code == 200

    missing = client.post("/query", json={"query": "q"})
    assert missing.status_code == 401


def test_invalid_api_key(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"good": "user"}
    client = TestClient(api_app)

    bad = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "bad"})
    assert bad.status_code == 401
