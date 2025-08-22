import asyncio
import time

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


def _setup(monkeypatch):
    cfg = ConfigModel(_env_file=None, _cli_parse_args=[])
    # allow all permissions for anonymous for simplicity
    cfg.api.role_permissions["anonymous"] = [
        "query",
        "metrics",
        "capabilities",
        "config",
        "health",
    ]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


def test_config_endpoints(monkeypatch, api_client):
    cfg = _setup(monkeypatch)

    resp = api_client.get("/config")
    assert resp.status_code == 200
    assert resp.json()["loops"] == cfg.loops

    resp = api_client.put("/config", json={"loops": 3})
    assert resp.status_code == 200
    assert resp.json()["loops"] == 3

    resp = api_client.post("/config", json={"loops": 5})
    assert resp.status_code == 200
    assert resp.json()["loops"] == 5

    resp = api_client.delete("/config")
    assert resp.status_code == 200


@pytest.mark.slow
def test_async_query_status(monkeypatch, api_client):
    _setup(monkeypatch)

    async def dummy_async(self, query, config, callbacks=None, **k):
        await asyncio.sleep(0.01)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query_async", dummy_async)

    resp = api_client.post("/query/async", json={"query": "hi"})
    assert resp.status_code == 200
    qid = resp.json()["query_id"]

    running = api_client.get(f"/query/{qid}")
    assert running.status_code == 200
    assert running.json()["status"] == "running"

    time.sleep(0.05)
    done = api_client.get(f"/query/{qid}")
    assert done.status_code == 200
    assert done.json()["answer"] == "ok"

    gone = api_client.get(f"/query/{qid}")
    assert gone.status_code == 404

    missing = api_client.get("/query/bad-id")
    assert missing.status_code == 404


def test_async_query_cancel(monkeypatch, api_client):
    _setup(monkeypatch)

    async def long_async(self, query, config, callbacks=None, **k):
        await asyncio.sleep(0.1)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query_async", long_async)

    resp = api_client.post("/query/async", json={"query": "hi"})
    assert resp.status_code == 200
    qid = resp.json()["query_id"]

    cancel = api_client.delete(f"/query/{qid}")
    assert cancel.status_code == 200

    gone = api_client.get(f"/query/{qid}")
    assert gone.status_code == 404

    missing = api_client.delete("/query/bad-id")
    assert missing.status_code == 404


def test_metrics_and_capabilities(monkeypatch, api_client):
    _setup(monkeypatch)

    assert api_client.get("/metrics").status_code == 200
    cap = api_client.get("/capabilities")
    assert cap.status_code == 200
    assert "llm_backends" in cap.json()


def test_openapi_lists_new_routes(monkeypatch, api_client):
    _setup(monkeypatch)
    schema = api_client.get("/openapi.json").json()
    assert "/config" in schema["paths"]
    assert "/query/async" in schema["paths"]
    assert "/query/{query_id}" in schema["paths"]


def test_health_endpoint(monkeypatch, api_client):
    """/health should return service status."""

    _setup(monkeypatch)

    resp = api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
