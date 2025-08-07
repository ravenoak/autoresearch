# flake8: noqa
from pytest_bdd import scenario, when, then, parsers, given
from unittest.mock import patch
import responses
import requests
import json

from .common_steps import app_running, app_running_with_default, application_running
from fastapi.testclient import TestClient
from autoresearch.api import app as api_app
from autoresearch.orchestration.state import QueryState
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.config.models import ConfigModel, APIConfig
from autoresearch.config.loader import ConfigLoader


@given("the Autoresearch application is running")
def _app_running_alias(tmp_path, monkeypatch):
    return application_running(tmp_path, monkeypatch)


@when(parsers.parse('I send a streaming query "{query}" to the API'))
def send_streaming_query(query, monkeypatch, api_client, bdd_context):
    def dummy_run_query(q, config, callbacks=None, **kwargs):
        agents = ["Synthesizer", "Contrarian"]
        if callbacks and "on_cycle_end" in callbacks:
            for idx, agent in enumerate(agents):
                state = QueryState(query=q, metadata={"agent": agent})
                callbacks["on_cycle_end"](idx, state)
        return QueryResponse(
            answer="ok",
            citations=[],
            reasoning=[],
            metrics={"agents": agents, "time_ms": 1},
        )

    cfg = ConfigModel(loops=2, api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)

    with api_client.stream("POST", "/query?stream=true", json={"query": query}) as resp:
        bdd_context["stream_status"] = resp.status_code
        bdd_context["stream_chunks"] = [line for line in resp.iter_lines()]


@then("the streaming response should contain multiple JSON lines")
def check_streaming_lines(bdd_context):
    assert bdd_context["stream_status"] == 200
    chunks = [json.loads(line) for line in bdd_context["stream_chunks"]]
    assert len(chunks) >= 3
    assert chunks[0]["metrics"]["agent"] == "Synthesizer"
    assert chunks[1]["metrics"]["agent"] == "Contrarian"
    assert chunks[-1]["answer"] == "ok"
    assert chunks[-1]["metrics"]["agents"] == ["Synthesizer", "Contrarian"]
    assert all("error" not in c for c in chunks)


@when(parsers.parse('I send a query with webhook URL "{url}" to the API'))
def send_query_with_webhook(url, monkeypatch, api_client, bdd_context):
    cfg = ConfigModel(api=APIConfig(webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(answer="ok", citations=[], reasoning=[], metrics={}),
    )
    with responses.RequestsMock() as rsps:
        rsps.post(url, status=200)
        monkeypatch.setattr(
            "autoresearch.api._notify_webhook",
            lambda u, r, timeout=5: requests.post(u, json=r.model_dump(), timeout=timeout),
        )
        resp = api_client.post("/query", json={"query": "hi", "webhook_url": url})
        bdd_context["api_status"] = resp.status_code
        bdd_context["webhook_calls"] = len(rsps.calls)


@then("the request should succeed")
def check_api_success(bdd_context):
    assert bdd_context["api_status"] == 200


@then("the webhook endpoint should be called")
def check_webhook_called(bdd_context):
    assert bdd_context["webhook_calls"] == 1


@scenario("../features/api_streaming_webhook.feature", "Streaming query responses")
def test_streaming_query_responses():
    pass


@scenario("../features/api_streaming_webhook.feature", "Webhook notifications on query completion")
def test_webhook_notifications():
    pass
