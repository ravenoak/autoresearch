import pytest

from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.models import QueryResponse


def _setup(monkeypatch):
    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = [
        "query",
        "metrics",
        "capabilities",
        "config",
        "health",
    ]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


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
    assert data["answer"] == "Machine learning is ..."
    assert data["citations"] == ["https://example.com"]
    assert data["reasoning"] == ["step 1", "step 2"]
    assert data["metrics"]["cycles_completed"] == 1


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
