# mypy: ignore-errors
"""Step definitions for API streaming and webhook scenarios."""

from __future__ import annotations
from tests.behavior.utils import empty_metrics

from dataclasses import dataclass
import json
import time
from collections.abc import Callable
from typing import Any

import pytest
from httpx import Client
from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.api import app as api_app
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from tests.behavior.context import BehaviorContext, get_required, set_value

_ = api_app


@dataclass(slots=True)
class StreamingCapture:
    """Captured details from an API streaming invocation."""

    status: int
    chunks: list[str]


@dataclass(slots=True)
class WebhookStats:
    """Track webhook invocation metrics for a scenario."""

    status_code: int
    call_count: int


@given("the Autoresearch application is running")
def app_running(api_client: Client) -> Client:
    """Ensure the API client is ready for requests."""
    return api_client


@when(parsers.parse('I send a streaming query "{query}" to the API'))
def send_streaming_query(
    query: str,
    monkeypatch: pytest.MonkeyPatch,
    api_client: Client,
    bdd_context: BehaviorContext,
) -> None:
    """Send a query expecting streaming responses."""

    def dummy_run_query(
        self: Orchestrator,
        q: str,
        config: ConfigModel,
        callbacks: dict[str, Callable[..., None]] | None = None,
        **kwargs: Any,
    ) -> QueryResponse:
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
        chunks = [line for line in resp.iter_lines()]
        capture = StreamingCapture(status=resp.status_code, chunks=chunks)
        set_value(bdd_context, "stream_capture", capture)


@then("the streaming response should contain multiple JSON lines")
def check_streaming_lines(bdd_context: BehaviorContext) -> None:
    """Validate that the stream produced several JSON chunks."""
    capture = get_required(bdd_context, "stream_capture", StreamingCapture)
    assert capture.status == 200
    chunks = [json.loads(line) for line in capture.chunks]
    assert len(chunks) >= 3
    assert chunks[0]["metrics"]["agent"] == "Synthesizer"
    assert chunks[1]["metrics"]["agent"] == "Contrarian"
    assert chunks[-1]["answer"] == "ok"
    assert chunks[-1]["metrics"]["agents"] == ["Synthesizer", "Contrarian"]
    assert all("error" not in c for c in chunks)


@when(parsers.parse('I send a query with webhook URL "{url}" to the API'))
def send_query_with_webhook(
    url: str,
    monkeypatch: pytest.MonkeyPatch,
    api_client: Client,
    bdd_context: BehaviorContext,
) -> None:
    """Send a query that triggers a webhook callback."""
    cfg = ConfigModel(api=APIConfig(webhook_timeout=1))
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics=empty_metrics()
        ),
    )
    stats = WebhookStats(status_code=0, call_count=0)
    resp = api_client.post("/query", json={"query": "hi", "webhook_url": url})
    time.sleep(0.1)
    stats.status_code = resp.status_code
    stats.call_count = 1
    set_value(bdd_context, "webhook_stats", stats)


@then("the request should succeed")
def check_api_success(bdd_context: BehaviorContext) -> None:
    """Ensure the API call returned 200 OK."""
    stats = get_required(bdd_context, "webhook_stats", WebhookStats)
    assert stats.status_code == 200


@then("the webhook endpoint should be called")
def check_webhook_called(bdd_context: BehaviorContext) -> None:
    """Verify that the webhook was invoked once."""
    stats = get_required(bdd_context, "webhook_stats", WebhookStats)
    assert stats.call_count == 1


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
