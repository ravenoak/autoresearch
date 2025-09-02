import json
import time

import pytest

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

    cfg = ConfigModel(api=APIConfig(webhooks=["http://hook"], webhook_timeout=0.1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
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
