"""Step definitions for asynchronous query API behavior tests."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from pytest_bdd import given, when, then, scenario, parsers

from autoresearch.api import app as api_app
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


@given("the API server is running")
def api_server_running(
    bdd_context: dict[str, Any],
    api_client,
    temp_config,
    isolate_network,
    restore_environment,
) -> None:
    """Provide an API client for interactions."""

    bdd_context["client"] = api_client


@when(parsers.parse('I submit an async query "{query}"'))
def submit_async_query(
    query: str,
    bdd_context: dict[str, Any],
    monkeypatch,
    dummy_query_response: QueryResponse,
    temp_config,
    isolate_network,
    restore_environment,
) -> None:
    """Submit an asynchronous query to the API."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    async def run_async(q: str, config: ConfigModel) -> QueryResponse:
        return dummy_query_response.model_copy(deep=True)

    monkeypatch.setattr(Orchestrator, "run_query_async", run_async)

    client = bdd_context["client"]
    resp = client.post("/query/async", json={"query": query})
    bdd_context["submit_response"] = resp
    if resp.status_code == 200:
        bdd_context["query_id"] = resp.json()["query_id"]


@then("the response should include a query ID")
def check_query_id(bdd_context: dict[str, Any]) -> None:
    """Ensure the async submission returned an identifier."""

    resp = bdd_context["submit_response"]
    assert resp.status_code == 200
    assert "query_id" in resp.json()


@when("I request the status for that query ID")
def request_status(bdd_context: dict[str, Any]) -> None:
    """Retrieve the result for the previously submitted query."""

    query_id = bdd_context["query_id"]
    future = api_app.state.async_tasks.get(query_id)
    if future is not None:
        while not future.done():
            time.sleep(0.01)
    client = bdd_context["client"]
    resp = client.get(f"/query/{query_id}")
    bdd_context["status_response"] = resp


@then("the response should contain an answer")
def check_answer(bdd_context: dict[str, Any]) -> None:
    """Verify the async query returned an answer."""

    resp = bdd_context["status_response"]
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("answer")


@given("an async query has been submitted")
def async_query_submitted(
    bdd_context: dict[str, Any],
    api_client,
    monkeypatch,
    dummy_query_response: QueryResponse,
    temp_config,
    isolate_network,
    restore_environment,
) -> None:
    """Submit a long-running async query for cancellation tests."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    async def run_async(q: str, config: ConfigModel) -> QueryResponse:
        await asyncio.sleep(0.1)
        return dummy_query_response.model_copy(deep=True)

    monkeypatch.setattr(Orchestrator, "run_query_async", run_async)

    resp = api_client.post("/query/async", json={"query": "slow"})
    bdd_context["client"] = api_client
    bdd_context["query_id"] = resp.json()["query_id"]


@when("I cancel the async query")
def cancel_async_query(bdd_context: dict[str, Any]) -> None:
    """Cancel the previously submitted asynchronous query."""

    query_id = bdd_context["query_id"]
    client = bdd_context["client"]
    resp = client.delete(f"/query/{query_id}")
    bdd_context["cancel_response"] = resp


@then("the response should indicate cancellation")
def check_cancellation(bdd_context: dict[str, Any]) -> None:
    """Ensure the async query was cancelled and cleaned up."""

    resp = bdd_context["cancel_response"]
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "cancelled"
    assert bdd_context["query_id"] not in api_app.state.async_tasks


@scenario(
    "../features/api_async_query.feature",
    "Submit async query and retrieve result",
)
def test_async_query_result() -> None:
    """Async query completes and returns a result."""
    return


@scenario(
    "../features/api_async_query.feature",
    "Cancel a running async query",
)
def test_async_query_cancellation() -> None:
    """Running async query can be cancelled."""
    return
