import asyncio
import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

import autoresearch.api as api
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryRequest, QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.types import CallbackMap


def _setup(monkeypatch: pytest.MonkeyPatch, cfg: ConfigModel) -> ConfigModel:
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


@pytest.mark.slow
def test_query_stream_param(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """/query should stream when stream=true is passed."""

    def dummy_run_query(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        **kwargs: object,
    ) -> QueryResponse:
        state = QueryState(query=query)
        for i in range(2):
            if callbacks and "on_cycle_end" in callbacks:
                callbacks["on_cycle_end"](i, state)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    cfg = ConfigModel(loops=2, api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    _setup(monkeypatch, cfg)
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)

    with api_client.stream("POST", "/query?stream=true", json={"query": "q"}) as resp:
        assert resp.status_code == 200
        chunks = [line for line in resp.iter_lines()]
    assert len(chunks) == 3


@pytest.mark.slow
def test_long_running_stream(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Streaming should handle long running operations without timing out."""

    def long_run_query(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        **kwargs: object,
    ) -> QueryResponse:
        state = QueryState(query=query)
        for i in range(3):
            time.sleep(0.05)
            if callbacks and "on_cycle_end" in callbacks:
                callbacks["on_cycle_end"](i, state)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    _setup(monkeypatch, cfg)
    monkeypatch.setattr(Orchestrator, "run_query", long_run_query)

    start = time.perf_counter()
    with api_client.stream("POST", "/query?stream=true", json={"query": "q"}) as resp:
        assert resp.status_code == 200
        chunks = [line for line in resp.iter_lines()]
    duration = time.perf_counter() - start
    assert len(chunks) == 4
    assert duration >= 0.15


@pytest.mark.slow
def test_config_webhooks(
    monkeypatch: pytest.MonkeyPatch,
    api_client: TestClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Configured webhooks should receive final results."""

    cfg = ConfigModel(api=APIConfig(webhooks=["http://hook"], webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    _setup(monkeypatch, cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )

    httpx_mock.add_response(method="POST", url="http://hook", status_code=200)
    resp = api_client.post("/query", json={"query": "hi"})
    assert resp.status_code == 200
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    req = requests[0]
    assert req.method == "POST"
    assert str(req.url) == "http://hook"
    payload = json.loads(req.content.decode())
    assert payload["answer"] == "ok"


@pytest.mark.slow
def test_webhook_retry(
    monkeypatch: pytest.MonkeyPatch,
    api_client: TestClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Webhook failures should be retried once."""

    attempts = {"count": 0}

    observed: list[tuple[float | int, int, float]] = []

    def notify_with_retry(
        url: str,
        result: QueryResponse,
        timeout: float | int,
        retries: int = 3,
        backoff: float = 0.5,
    ) -> None:
        observed.append((timeout, retries, backoff))
        for _ in range(retries):
            attempts["count"] += 1
            try:
                resp = httpx.post(url, json=result.model_dump(), timeout=timeout)
                resp.raise_for_status()
                return
            except (httpx.RequestError, httpx.HTTPStatusError):
                continue

    cfg = ConfigModel(api=APIConfig(webhooks=["http://hook"], webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    _setup(monkeypatch, cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )
    monkeypatch.setattr("autoresearch.api.webhooks.notify_webhook", notify_with_retry)
    httpx_mock.add_response(method="POST", url="http://hook", status_code=500)
    httpx_mock.add_response(method="POST", url="http://hook", status_code=200)

    resp = api_client.post("/query", json={"query": "hi"})
    assert resp.status_code == 200
    assert attempts["count"] == 2
    assert observed == [(1, 3, 0.5)]
    assert len(httpx_mock.get_requests()) == 2


@pytest.mark.slow
def test_batch_query_pagination(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """/query/batch should honor page and page_size parameters."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    _setup(monkeypatch, cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer=q, citations=[], reasoning=[], metrics={}
        ),
    )

    payload = {"queries": [{"query": "q1"}, {"query": "q2"}, {"query": "q3"}, {"query": "q4"}]}
    resp = api_client.post("/query/batch?page=2&page_size=2", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["answer"] == "q3"


@pytest.mark.slow
def test_batch_query_defaults(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """/query/batch should use default pagination when params are omitted."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    _setup(monkeypatch, cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer=q, citations=[], reasoning=[], metrics={}
        ),
    )

    payload = {"queries": [{"query": "a"}, {"query": "b"}, {"query": "c"}]}
    resp = api_client.post("/query/batch", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert [r["answer"] for r in data["results"]] == ["a", "b", "c"]


def test_api_key_roles_integration(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Requests should succeed only with valid API keys."""

    cfg = ConfigModel(api=APIConfig(api_keys={"secret": "admin"}))
    cfg.api.role_permissions["anonymous"] = ["query"]
    _setup(monkeypatch, cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )

    resp = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "secret"})
    assert resp.status_code == 200
    missing = api_client.post("/query", json={"query": "q"})
    assert missing.status_code == 401
    assert missing.json()["detail"] == "Missing API key"
    bad = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "bad"})
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid API key"


def test_stream_requires_api_key(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """/query/stream rejects requests lacking a valid API key."""

    def dummy_run_query(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        **k: object,
    ) -> QueryResponse:
        state = QueryState(query=query)
        if callbacks and "on_cycle_end" in callbacks:
            callbacks["on_cycle_end"](0, state)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    cfg = ConfigModel(api=APIConfig(api_key="secret"))
    _setup(monkeypatch, cfg)
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)

    unauth = api_client.post("/query/stream", json={"query": "q"})
    assert unauth.status_code == 401
    assert unauth.headers["WWW-Authenticate"] == "API-Key"
    assert unauth.json()["detail"] == "Missing API key"

    with api_client.stream(
        "POST", "/query/stream", json={"query": "q"}, headers={"X-API-Key": "secret"}
    ) as resp:
        assert resp.status_code == 200

    bad = api_client.post("/query/stream", json={"query": "q"}, headers={"X-API-Key": "bad"})
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid API key"
    assert bad.headers["WWW-Authenticate"] == "API-Key"


def test_batch_query_async_order(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """/query/batch should process queries concurrently while preserving order."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    _setup(monkeypatch, cfg)

    async def fake_query_endpoint(q: QueryRequest) -> QueryResponse:
        await asyncio.sleep(0.01)
        return QueryResponse(answer=q.query, citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(api, "query_endpoint", fake_query_endpoint)
    payload = {"queries": [{"query": "a"}, {"query": "b"}, {"query": "c"}]}
    start = time.perf_counter()
    resp = api_client.post("/query/batch?page=1&page_size=3", json=payload)
    duration = time.perf_counter() - start
    assert resp.status_code == 200
    assert [r["answer"] for r in resp.json()["results"]] == ["a", "b", "c"]
    assert duration < 0.03
