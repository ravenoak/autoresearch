import json
import time

import pytest
from fastapi.testclient import TestClient

import autoresearch.api as api
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
import autoresearch.api.streaming as streaming_module


@pytest.mark.slow
def test_stream_emits_keepalive(monkeypatch, api_client):
    """Long-running queries should keep streams alive with heartbeat lines."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    def long_query(self, query, config, callbacks=None, **kwargs):
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
def test_stream_webhook_partial(monkeypatch, api_client):
    """Streaming should POST each partial result to the webhook."""

    cfg = ConfigModel(api=APIConfig(webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    calls = []

    def fake_notify(url, result, timeout, retries=3, backoff=0.5):  # noqa: D401
        calls.append(result.answer)

    def run_query(self, query, config, callbacks=None, **kwargs):
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

    assert calls == ["partial-0", "partial-1", "final"]


@pytest.mark.slow
def test_streaming_error_triggers_webhook(monkeypatch, httpx_mock):
    """Errors in streaming queries should still trigger webhook delivery."""

    cfg = ConfigModel(api=APIConfig(webhooks=["http://hook"], webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg, raising=False)
    loader = ConfigLoader.new_for_tests()
    app = api.create_app(loader)
    client = TestClient(app)

    def failing_query(self, query, config, callbacks=None, **kwargs):
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
