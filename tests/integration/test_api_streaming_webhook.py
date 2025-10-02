import json
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

import autoresearch.api as api
import autoresearch.api.streaming as streaming_module
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


@pytest.mark.slow
def test_stream_emits_keepalive(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Long-running queries should keep streams alive with heartbeat lines."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    def long_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        callbacks: dict[str, Any] | None = None,
        **kwargs: object,
    ) -> QueryResponse:
        time.sleep(0.2)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", long_query)
    monkeypatch.setattr(streaming_module, "KEEPALIVE_INTERVAL", 0.05)

    with api_client.stream("POST", "/query?stream=true", json={"query": "q"}) as resp:
        assert resp.status_code == 200
        lines = [line for line in resp.iter_lines()]

    assert lines[0] == ""
    assert json.loads(lines[-1])["answer"] == "ok"


@pytest.mark.slow
def test_stream_webhook_final_only(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Streaming should POST only the final result to the webhook."""

    cfg = ConfigModel(api=APIConfig(webhook_timeout=1, webhook_retries=2, webhook_backoff=0.1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    api.config_loader._config = cfg
    monkeypatch.setattr(streaming_module, "get_config", lambda: cfg)

    calls: list[tuple[str, float | int, int, float]] = []

    def fake_notify(
        url: str,
        result: QueryResponse,
        timeout: float | int,
        retries: int = 3,
        backoff: float = 0.5,
    ) -> None:
        calls.append((result.answer, timeout, retries, backoff))

    def run_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        callbacks: dict[str, Any] | None = None,
        **kwargs: object,
    ) -> QueryResponse:
        from autoresearch.orchestration.state import QueryState

        state = QueryState(query=query)
        for i in range(2):
            state.results["final_answer"] = f"partial-{i}"
            if callbacks and "on_cycle_end" in callbacks:
                callbacks["on_cycle_end"](i, state)
        return QueryResponse(answer="final", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", run_query)
    monkeypatch.setattr("autoresearch.api.webhooks.notify_webhook", fake_notify)

    with api_client.stream(
        "POST", "/query?stream=true", json={"query": "q", "webhook_url": "http://hook"}
    ) as resp:
        assert resp.status_code == 200
        [line for line in resp.iter_lines()]

    assert calls == [("final", 1, 2, 0.1)]


@pytest.mark.slow
def test_streaming_error_triggers_webhook(
    monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock
) -> None:
    """Errors in streaming queries should still trigger webhook delivery."""

    cfg = ConfigModel(api=APIConfig(webhooks=["http://hook"], webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg, raising=False)
    loader = ConfigLoader.new_for_tests()
    app = api.create_app(loader)
    client = TestClient(app)

    def failing_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        callbacks: dict[str, Any] | None = None,
        **kwargs: object,
    ) -> QueryResponse:
        raise RuntimeError("boom")

    monkeypatch.setattr(Orchestrator, "run_query", failing_query)
    httpx_mock.add_response(method="POST", url="http://hook", status_code=200)

    with client.stream("POST", "/query?stream=true", json={"query": "q"}) as resp:
        assert resp.status_code == 200
        lines = [line for line in resp.iter_lines() if line]

    time.sleep(0.1)
    assert json.loads(lines[-1])["answer"].startswith("Error:")
    req = httpx_mock.get_requests()[0]
    payload = json.loads(req.content.decode())
    assert payload["answer"].startswith("Error:")
