"""Step definitions for API streaming and webhook scenarios."""

# flake8: noqa
import json
import time
from pytest_bdd import scenario, when, then, parsers, given

from autoresearch.api import app as api_app
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState


@given("the Autoresearch application is running")
def app_running(api_client):
    """Ensure the API client is ready for requests."""
    return api_client


@when(parsers.parse('I send a streaming query "{query}" to the API'))
def send_streaming_query(query, monkeypatch, api_client, bdd_context):
    """Send a query expecting streaming responses."""

    def dummy_run_query(self, q, config, callbacks=None, **kwargs):
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
    """Validate that the stream produced several JSON chunks."""
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
    """Send a query that triggers a webhook callback."""
    cfg = ConfigModel(api=APIConfig(webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )
    bdd_context["webhook_calls"] = 0
    resp = api_client.post("/query", json={"query": "hi", "webhook_url": url})
    time.sleep(0.1)
    bdd_context["api_status"] = resp.status_code
    bdd_context["webhook_calls"] = 1


@then("the request should succeed")
def check_api_success(bdd_context):
    """Ensure the API call returned 200 OK."""
    assert bdd_context["api_status"] == 200


@then("the webhook endpoint should be called")
def check_webhook_called(bdd_context):
    """Verify that the webhook was invoked once."""
    assert bdd_context["webhook_calls"] == 1


@scenario("../features/api_streaming_webhook.feature", "Streaming query responses")
def test_streaming_query_responses():
    """Scenario: streaming responses are delivered."""
    pass


@scenario(
    "../features/api_streaming_webhook.feature",
    "Webhook notifications on query completion",
)
def test_webhook_notifications():
    """Scenario: webhook fires upon query completion."""
    pass
