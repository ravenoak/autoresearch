import pytest

from autoresearch.api import utils as api_utils
from autoresearch.api.models import QueryResponseV1
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState


def _setup(monkeypatch):
    cfg = ConfigModel(api=APIConfig())
    ConfigLoader.reset_instance()
    cfg.api.role_permissions["anonymous"] = [
        "query",
        "metrics",
        "capabilities",
        "config",
        "health",
    ]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


def test_docs_endpoints_require_auth(monkeypatch, api_client):
    cfg = ConfigModel(api=APIConfig(api_key="secret"))
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    assert api_client.get("/docs").status_code == 401
    bad = api_client.get("/docs", headers={"X-API-Key": "bad"})
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid API key"
    assert bad.headers["WWW-Authenticate"] == "API-Key"
    ok = api_client.get("/docs", headers={"X-API-Key": "secret"})
    assert ok.status_code == 200

    openapi = api_client.get("/openapi.json", headers={"X-API-Key": "secret"})
    assert openapi.status_code == 200


def test_docs_permission_denied(monkeypatch, api_client):
    cfg = ConfigModel(api=APIConfig(api_keys={"u": "user"}))
    cfg.api.role_permissions = {"user": []}
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    resp = api_client.get("/docs", headers={"X-API-Key": "u"})

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Insufficient permissions"


def test_query_endpoint(monkeypatch, api_client):
    _setup(monkeypatch)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda *a, **k: QueryResponse(
            answer="Machine learning is ...",
            citations=["https://example.com"],
            reasoning=["step 1", "step 2"],
            metrics={
                "cycles_completed": 1,
                "total_tokens": {"input": 5, "output": 7, "total": 12},
            },
        ),
    )
    resp = api_client.post("/query", json={"query": "Explain ML"})
    assert resp.status_code == 200
    data = resp.json()
    parsed = QueryResponseV1.model_validate(data)
    assert parsed.answer == "Machine learning is ..."
    assert parsed.citations == ["https://example.com"]
    assert parsed.reasoning == ["step 1", "step 2"]
    assert parsed.metrics["cycles_completed"] == 1
    assert parsed.version == "1"


@pytest.mark.slow
def test_stream_endpoint(monkeypatch, api_client):
    _setup(monkeypatch)

    def dummy_run_query(query, config, callbacks=None, **k):
        state = QueryState(query=query)
        if callbacks and "on_cycle_end" in callbacks:
            callbacks["on_cycle_end"](0, state)
            callbacks["on_cycle_end"](1, state)
        return QueryResponse(
            answer="Machine learning is ...",
            citations=["https://example.com"],
            reasoning=["step 1", "step 2"],
            metrics={"cycles_completed": 1},
        )

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    with api_client.stream("POST", "/query/stream", json={"query": "Explain"}) as resp:
        assert resp.status_code == 200
        chunks = [line for line in resp.iter_lines()]
    assert len(chunks) == 3


def test_batch_endpoint(monkeypatch, api_client):
    _setup(monkeypatch)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer=q, citations=[], reasoning=[], metrics={}
        ),
    )
    payload = {"queries": [{"query": "a"}, {"query": "b"}, {"query": "c"}]}
    resp = api_client.post("/query/batch?page=1&page_size=2", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert len(data["results"]) == 2


def test_async_query_status_schema(monkeypatch, api_client):
    _setup(monkeypatch)

    async def dummy_run_query_async(*a, **k):
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query_async", dummy_run_query_async)

    start = api_client.post("/query/async", json={"query": "hi"})
    assert start.status_code == 200
    qid = start.json()["query_id"]

    resp = api_client.get(f"/query/{qid}")
    assert resp.status_code == 200
    data = resp.json()
    parsed = QueryResponseV1.model_validate(data)
    assert parsed.version == "1"
    assert parsed.answer == "ok"


def test_unknown_version_rejected(monkeypatch, api_client):
    _setup(monkeypatch)
    resp = api_client.post("/query", json={"query": "hi", "version": "99"})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Unsupported API version 99"


def test_deprecated_version_rejected(monkeypatch, api_client):
    _setup(monkeypatch)
    monkeypatch.setattr(api_utils, "DEPRECATED_VERSIONS", {"0"})
    resp = api_client.post("/query", json={"query": "hi", "version": "0"})
    assert resp.status_code == 410
    assert resp.json()["detail"] == "API version 0 is deprecated"


def test_metrics_endpoint(monkeypatch, api_client):
    _setup(monkeypatch)
    resp = api_client.get("/metrics")
    assert resp.status_code == 200
    assert "autoresearch_queries_total" in resp.text


def test_capabilities_endpoint(monkeypatch, api_client):
    _setup(monkeypatch)
    resp = api_client.get("/capabilities")
    assert resp.status_code == 200
    body = resp.json()
    assert "llm_backends" in body
    assert "version" in body


def test_health_endpoint(monkeypatch, api_client):
    _setup(monkeypatch)
    resp = api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
