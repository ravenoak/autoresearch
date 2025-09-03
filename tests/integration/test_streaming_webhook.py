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

    def long_query(query, config, callbacks=None, **kwargs):
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
def test_webhook_retries(monkeypatch, api_client, httpx_mock):
    """Webhook delivery should be retried on failure."""

    cfg = ConfigModel(api=APIConfig(webhooks=["http://hook"], webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    api_client.app.state.config_loader._config = cfg
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )

    httpx_mock.add_response(method="POST", url="http://hook", status_code=500)
    httpx_mock.add_response(method="POST", url="http://hook", status_code=200)

    resp = api_client.post("/query", json={"query": "hi"})
    assert resp.status_code == 200
    assert len(httpx_mock.get_requests()) == 2


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
