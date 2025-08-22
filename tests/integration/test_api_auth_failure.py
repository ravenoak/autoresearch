import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel


def _setup(monkeypatch):
    cfg = ConfigModel(api=APIConfig())
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


def test_invalid_bearer_token(monkeypatch, api_client):
    """Invalid bearer token should return 401."""
    cfg = _setup(monkeypatch)
    cfg.api.bearer_token = "secret"
    resp = api_client.post(
        "/query", json={"query": "q"}, headers={"Authorization": "Bearer wrong"}
    )
    assert resp.status_code == 401


def test_permission_denied(monkeypatch, api_client):
    """API key lacking permission results in 403."""
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"u": "user"}
    cfg.api.role_permissions = {"user": ["query"]}
    resp = api_client.get("/metrics", headers={"X-API-Key": "u"})
    assert resp.status_code == 403
