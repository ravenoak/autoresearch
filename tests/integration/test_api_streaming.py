from fastapi.testclient import TestClient

from autoresearch.api import app as api_app
from autoresearch.config.models import ConfigModel, APIConfig
from autoresearch.config.loader import ConfigLoader
import asyncio
import time
import pytest

from autoresearch.models import QueryResponse, QueryRequest
import autoresearch.api as api
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState


def test_query_stream_param(monkeypatch):
    """/query should stream when stream=true is passed."""

    def dummy_run_query(query, config, callbacks=None, **kwargs):
        state = QueryState(query=query)
        for i in range(2):
            if callbacks and "on_cycle_end" in callbacks:
                callbacks["on_cycle_end"](i, state)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    cfg = ConfigModel(loops=2, api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    client = TestClient(api_app)

    with client.stream("POST", "/query?stream=true", json={"query": "q"}) as resp:
        assert resp.status_code == 200
        chunks = [line for line in resp.iter_lines()]
    assert len(chunks) == 3


@pytest.mark.skip(reason="requires httpx_mock fixture")
def test_config_webhooks(monkeypatch, httpx_mock):
    """Configured webhooks should receive final results."""

    cfg = ConfigModel(api=APIConfig(webhooks=["http://hook"], webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(answer="ok", citations=[], reasoning=[], metrics={}),
    )
    client = TestClient(api_app)

    httpx_mock.add_response(method="POST", url="http://hook", status_code=200)
    resp = client.post("/query", json={"query": "hi"})
    assert resp.status_code == 200
    assert len(httpx_mock.get_requests()) == 1


def test_batch_query_pagination(monkeypatch):
    """/query/batch should honor page and page_size parameters."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(answer=q, citations=[], reasoning=[], metrics={}),
    )
    client = TestClient(api_app)

    payload = {"queries": [{"query": "q1"}, {"query": "q2"}, {"query": "q3"}, {"query": "q4"}]}
    resp = client.post("/query/batch?page=2&page_size=2", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["answer"] == "q3"


def test_batch_query_defaults(monkeypatch):
    """/query/batch should use default pagination when params are omitted."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(answer=q, citations=[], reasoning=[], metrics={}),
    )
    client = TestClient(api_app)

    payload = {"queries": [{"query": "a"}, {"query": "b"}, {"query": "c"}]}
    resp = client.post("/query/batch", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert [r["answer"] for r in data["results"]] == ["a", "b", "c"]


def test_api_key_roles_integration(monkeypatch):
    """Requests should succeed only with valid API keys."""

    cfg = ConfigModel(api=APIConfig(api_keys={"secret": "admin"}))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(answer="ok", citations=[], reasoning=[], metrics={}),
    )
    client = TestClient(api_app)

    resp = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "secret"})
    assert resp.status_code == 200

    bad = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "bad"})
    assert bad.status_code == 401


def test_batch_query_async_order(monkeypatch):
    """/query/batch should process queries concurrently while preserving order."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    async def fake_query_endpoint(q: QueryRequest) -> QueryResponse:
        await asyncio.sleep(0.01)
        return QueryResponse(answer=q.query, citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(api, "query_endpoint", fake_query_endpoint)
    client = TestClient(api_app)

    payload = {"queries": [{"query": "a"}, {"query": "b"}, {"query": "c"}]}
    start = time.perf_counter()
    resp = client.post("/query/batch?page=1&page_size=3", json=payload)
    duration = time.perf_counter() - start
    assert resp.status_code == 200
    assert [r["answer"] for r in resp.json()["results"]] == ["a", "b", "c"]
    assert duration < 0.03
