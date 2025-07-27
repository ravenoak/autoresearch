from fastapi.testclient import TestClient

from autoresearch.api import app
from autoresearch.config import ConfigModel, APIConfig
from autoresearch.orchestration.orchestrator import Orchestrator


def _setup(monkeypatch):
    cfg = ConfigModel.model_construct(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr("autoresearch.api.get_config", lambda: cfg)
    monkeypatch.setattr("autoresearch.api._notify_webhook", lambda u, r, timeout=5: None)
    return cfg


def test_query_endpoint_runtime_error(monkeypatch):
    _setup(monkeypatch)

    def raise_error(q, c):
        raise RuntimeError("fail")

    monkeypatch.setattr(Orchestrator, "run_query", raise_error)
    client = TestClient(app)
    resp = client.post("/query", json={"query": "q"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"].startswith("Error: fail")
    assert data["metrics"]["error"] == "fail"


def test_query_endpoint_invalid_response(monkeypatch):
    _setup(monkeypatch)
    monkeypatch.setattr(Orchestrator, "run_query", lambda q, c: {"foo": "bar"})
    client = TestClient(app)
    resp = client.post("/query", json={"query": "q"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Error: Invalid response format"
    assert data["metrics"]["error"] == "Invalid response format"
