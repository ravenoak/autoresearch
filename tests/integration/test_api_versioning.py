"""Integration tests for versioned API schemas."""

import pytest
from fastapi.testclient import TestClient

from autoresearch.api.models import QueryResponseV1
from autoresearch.config import APIConfig, ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator


def _setup(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ConfigModel(api=APIConfig())
    ConfigLoader.reset_instance()
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)


def test_rejects_unknown_version(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Requests with an unsupported version fail validation."""
    _setup(monkeypatch)
    resp = api_client.post("/query", json={"query": "hi", "version": "2"})
    assert resp.status_code == 422


def test_batch_response_includes_version(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Batch endpoint wraps responses with a version field."""
    _setup(monkeypatch)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponseV1(
            answer=q, citations=[], reasoning=[], metrics={}
        ),
    )
    payload = {"queries": [{"query": "a"}, {"query": "b"}]}
    resp = api_client.post("/query/batch", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1"


def test_async_endpoint_returns_version(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Async query acknowledgements include the schema version."""
    _setup(monkeypatch)

    class Dummy:
        async def run_query_async(
            self, query: str, config: ConfigModel
        ) -> QueryResponseV1:
            return QueryResponseV1(answer=query, citations=[], reasoning=[], metrics={})

    monkeypatch.setattr("autoresearch.api.routing.create_orchestrator", lambda: Dummy())
    resp = api_client.post("/query/async", json={"query": "hi"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1"
    assert "query_id" in body
