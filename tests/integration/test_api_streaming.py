import responses
from fastapi.testclient import TestClient

from autoresearch.api import app as api_app
from autoresearch.config import ConfigModel, ConfigLoader, APIConfig
from autoresearch.models import QueryResponse
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


def test_config_webhooks(monkeypatch):
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

    with responses.RequestsMock() as rsps:
        rsps.post("http://hook", status=200)
        resp = client.post("/query", json={"query": "hi"})
        assert resp.status_code == 200
        assert len(rsps.calls) == 1


def test_batch_query_pagination(monkeypatch):
    """/query/batch should honor page and page_size parameters."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(answer=q.query, citations=[], reasoning=[], metrics={}),
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
