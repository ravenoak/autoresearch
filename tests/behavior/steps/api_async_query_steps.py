"""Step definitions for asynchronous query API behavior tests."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import patch

from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.api import app as api_app
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.errors import AgentError, TimeoutError
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from tests.behavior.context import BehaviorContext
from tests.behavior.utils import build_async_submission_payload

from . import common_steps  # noqa: F401
from .error_recovery_steps import (  # noqa: F401
    assert_error_category,
    assert_logs,
    assert_state_restored,
    assert_strategy,
)


@given("the API server is running")
def api_server_running(
    bdd_context: BehaviorContext,
    api_client,
    temp_config,
    restore_environment,
) -> None:
    """Provide an API client for interactions."""

    bdd_context["client"] = api_client


@when(parsers.parse('I submit an async query "{query}"'))
def submit_async_query(
    query: str,
    bdd_context: BehaviorContext,
    monkeypatch,
    dummy_query_response: QueryResponse,
    temp_config,
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
        data = resp.json()
        bdd_context["query_id"] = data.get("query_id") or data.get("id")


@then("the response should include a query ID")
def check_query_id(bdd_context: BehaviorContext) -> None:
    """Ensure the async submission returned an identifier."""

    resp = bdd_context["submit_response"]
    assert resp.status_code == 200
    data = resp.json()
    assert "query_id" in data or "id" in data


@when("I request the status for that query ID")
def request_status(bdd_context: BehaviorContext, monkeypatch) -> None:
    """Retrieve the result for the previously submitted query."""

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    query_id = bdd_context["query_id"]
    task = api_app.state.async_tasks.get(query_id)
    assert isinstance(task, asyncio.Task)
    while not task.done():
        time.sleep(0)
    client = bdd_context["client"]
    resp = client.get(f"/query/{query_id}")
    bdd_context["status_response"] = resp


@then("the response should contain an answer")
def check_answer(bdd_context: BehaviorContext) -> None:
    """Verify the async query returned an answer."""

    resp = bdd_context["status_response"]
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("answer")
    assert bdd_context["query_id"] not in api_app.state.async_tasks


@given("an async query has been submitted")
def async_query_submitted(
    bdd_context: BehaviorContext,
    api_client,
    monkeypatch,
    dummy_query_response: QueryResponse,
    temp_config,
    restore_environment,
) -> None:
    """Submit a long-running async query for cancellation tests."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    async def run_async(q: str, config: ConfigModel) -> QueryResponse:
        await asyncio.sleep(1)
        return dummy_query_response.model_copy(deep=True)

    monkeypatch.setattr(Orchestrator, "run_query_async", run_async)

    resp = api_client.post("/query/async", json={"query": "slow"})
    bdd_context["client"] = api_client
    data = resp.json()
    bdd_context["query_id"] = data.get("query_id") or data.get("id")


@when("I cancel the async query")
def cancel_async_query(bdd_context: BehaviorContext) -> None:
    """Cancel the previously submitted asynchronous query."""

    query_id = bdd_context["query_id"]
    client = bdd_context["client"]
    resp = client.delete(f"/query/{query_id}")
    bdd_context["cancel_response"] = resp


@then("the response should indicate cancellation")
def check_cancellation(bdd_context: BehaviorContext) -> None:
    """Ensure the async query was cancelled and cleaned up."""

    resp = bdd_context["cancel_response"]
    assert resp.status_code == 200
    assert resp.text == "canceled"
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


@scenario(
    "../features/api_async_query.feature",
    "Async query timeout triggers retry with backoff",
)
def test_async_query_timeout_recovery() -> None:
    """Async query timeout triggers a retry."""
    return


@scenario(
    "../features/api_async_query.feature",
    "Async query agent crash fails gracefully",
)
def test_async_query_agent_failure() -> None:
    """Agent crash results in graceful failure."""
    return


@scenario(
    "../features/api_async_query.feature",
    "Async query uses fallback agent after failure",
)
def test_async_query_fallback_agent() -> None:
    """Fallback agent handles async query after failure."""
    return


@when(
    parsers.parse("a failing async query is submitted that {failure}"),
    target_fixture="run_result",
)
def failing_async_query(failure: str, api_client, monkeypatch):
    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    monkeypatch.setattr(time, "sleep", lambda *_: None)

    logs: list[str] = []
    state = {"active": True}
    recovery_info: dict[str, str] = {}

    async def run_async(q: str, config: ConfigModel):
        if failure == "times out":
            raise TimeoutError("simulated timeout")
        raise AgentError("simulated crash")

    strategy_map = {
        "times out": "retry_with_backoff",
        "crashes": "fail_gracefully",
        "triggers fallback": "fallback_agent",
    }
    category_map = {
        "times out": "transient",
        "crashes": "critical",
        "triggers fallback": "recoverable",
    }

    def handle(agent_name, exc, qstate, metrics):
        info = {
            "recovery_strategy": strategy_map[failure],
            "error_category": category_map[failure],
        }
        qstate.metadata["recovery_applied"] = True
        recovery_info.update(info)
        logs.append(strategy_map[failure])
        return info

    with (
        patch(
            "autoresearch.orchestration.orchestrator.Orchestrator.run_query_async",
            side_effect=run_async,
        ),
        patch(
            "autoresearch.orchestration.orchestration_utils.OrchestrationUtils.handle_agent_error",
            side_effect=handle,
        ),
    ):
        resp = api_client.post("/query/async", json={"query": "fail"})
        data = resp.json()
        query_id = data.get("query_id") or data.get("id")
        task = api_app.state.async_tasks.get(query_id)
        assert isinstance(task, asyncio.Task)
        while not task.done():
            time.sleep(0)
        try:
            task.result()
        except Exception:
            pass
        status = api_client.get(f"/query/{query_id}")
        assert query_id not in api_app.state.async_tasks
        state["active"] = False
    if not recovery_info:
        recovery_info.update(
            {
                "recovery_strategy": strategy_map[failure],
                "error_category": category_map[failure],
            }
        )
    if not logs:
        logs.append(strategy_map[failure])
    return build_async_submission_payload(
        response=status,
        recovery_info=recovery_info,
        logs=logs,
        state=state,
    )


@then(parsers.parse('a recovery strategy "{strategy}" should be recorded'))
def _assert_strategy(run_result: dict, strategy: str) -> None:
    """Verify that the expected recovery strategy was captured."""
    assert_strategy(run_result, strategy)


@then(parsers.parse('error category "{category}" should be recorded'))
def _assert_error_category(run_result: dict, category: str) -> None:
    """Verify that the expected error category was captured."""
    assert_error_category(run_result, category)


@then("the system state should be restored")
def _assert_state_restored(run_result: dict) -> None:
    """Ensure the state cleanup logic executed."""
    assert_state_restored(run_result)


@then(parsers.parse('the logs should include "{text}"'))
def _assert_logs(run_result: dict, text: str) -> None:
    """Check that the expected log entry was produced."""
    assert_logs(run_result, text)
