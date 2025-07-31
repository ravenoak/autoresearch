from fastapi.testclient import TestClient

from autoresearch.api import app as api_app
from autoresearch.config.models import ConfigModel, APIConfig
from autoresearch.config.loader import ConfigLoader


def _setup(monkeypatch):
    cfg = ConfigModel(api=APIConfig())
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


def test_invalid_bearer_token(monkeypatch):
    """Invalid bearer token should return 401."""
    cfg = _setup(monkeypatch)
    cfg.api.bearer_token = "secret"
    client = TestClient(api_app)
    resp = client.post("/query", json={"query": "q"}, headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


def test_permission_denied(monkeypatch):
    """API key lacking permission results in 403."""
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"u": "user"}
    cfg.api.role_permissions = {"user": ["query"]}
    client = TestClient(api_app)
    resp = client.get("/metrics", headers={"X-API-Key": "u"})
    assert resp.status_code == 403
