from fastapi.testclient import TestClient

from autoresearch.api import app, dynamic_limit
from autoresearch.config import ConfigModel, ConfigLoader, APIConfig
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


def _setup(monkeypatch):
    cfg = ConfigModel(api=APIConfig())
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(answer="ok", citations=[], reasoning=[], metrics={}),
    )
    return cfg


def test_dynamic_limit(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 5
    assert dynamic_limit() == "5/minute"
    cfg.api.rate_limit = 0
    assert dynamic_limit() == "1000000/minute"


def test_api_key_roles(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"secret": "user"}
    client = TestClient(app)

    resp = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "secret"})
    assert resp.status_code == 200

    resp = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "bad"})
    assert resp.status_code == 401


def test_batch_query_invalid_page(monkeypatch):
    _setup(monkeypatch)
    client = TestClient(app)
    payload = {"queries": [{"query": "q1"}]}
    resp = client.post("/query/batch?page=0&page_size=1", json=payload)
    assert resp.status_code == 400
