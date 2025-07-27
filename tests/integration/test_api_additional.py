from autoresearch.api import app as api_app
from autoresearch.config import ConfigModel, ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse
from fastapi.testclient import TestClient
import asyncio
import time


def _setup(monkeypatch):
    cfg = ConfigModel(_env_file=None, _cli_parse_args=[])
    # allow all permissions for anonymous for simplicity
    cfg.api.role_permissions["anonymous"] = ["query", "metrics", "capabilities"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


def test_config_endpoints(monkeypatch):
    cfg = _setup(monkeypatch)
    client = TestClient(api_app)

    resp = client.get("/config")
    assert resp.status_code == 200
    assert resp.json()["loops"] == cfg.loops

    resp = client.put("/config", json={"loops": 3})
    assert resp.status_code == 200
    assert resp.json()["loops"] == 3

    resp = client.post("/config", json={"loops": 5})
    assert resp.status_code == 200
    assert resp.json()["loops"] == 5

    resp = client.delete("/config")
    assert resp.status_code == 200


def test_async_query_status(monkeypatch):
    _setup(monkeypatch)

    async def dummy_async(query, config, callbacks=None, **k):
        await asyncio.sleep(0.01)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query_async", dummy_async)
    client = TestClient(api_app)

    resp = client.post("/query/async", json={"query": "hi"})
    assert resp.status_code == 200
    qid = resp.json()["query_id"]

    running = client.get(f"/query/{qid}")
    assert running.status_code == 200
    assert running.json()["status"] == "running"

    time.sleep(0.05)
    done = client.get(f"/query/{qid}")
    assert done.status_code == 200
    assert done.json()["answer"] == "ok"

    gone = client.get(f"/query/{qid}")
    assert gone.status_code == 404

    missing = client.get("/query/bad-id")
    assert missing.status_code == 404


def test_async_query_cancel(monkeypatch):
    _setup(monkeypatch)

    async def long_async(query, config, callbacks=None, **k):
        await asyncio.sleep(0.1)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query_async", long_async)
    client = TestClient(api_app)

    resp = client.post("/query/async", json={"query": "hi"})
    assert resp.status_code == 200
    qid = resp.json()["query_id"]

    cancel = client.delete(f"/query/{qid}")
    assert cancel.status_code == 200

    gone = client.get(f"/query/{qid}")
    assert gone.status_code == 404

    missing = client.delete("/query/bad-id")
    assert missing.status_code == 404


def test_metrics_and_capabilities(monkeypatch):
    _setup(monkeypatch)
    client = TestClient(api_app)

    assert client.get("/metrics").status_code == 200
    cap = client.get("/capabilities")
    assert cap.status_code == 200
    assert "llm_backends" in cap.json()


def test_openapi_lists_new_routes(monkeypatch):
    _setup(monkeypatch)
    client = TestClient(api_app)
    schema = client.get("/openapi.json").json()
    assert "/config" in schema["paths"]
    assert "/query/async" in schema["paths"]
    assert "/query/{query_id}" in schema["paths"]


def test_health_endpoint(monkeypatch):
    """/health should return service status."""

    _setup(monkeypatch)
    client = TestClient(api_app)

    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
