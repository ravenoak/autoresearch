"""Step definitions for batch query API behavior tests."""

from __future__ import annotations

from typing import Any, cast

import pytest
from pytest_bdd import given, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse
from tests.behavior.context import BehaviorContext
from tests.behavior.utils import PayloadDict, as_payload, store_payload

from . import common_steps  # noqa: F401


@given("the API server is running")
def api_server_running(
    test_context: BehaviorContext, api_client: Any
) -> None:
    """Provide a test client for API interactions."""
    test_context["client"] = api_client


@scenario(
    "../features/api_batch_query.feature",
    "Successful batch submission returning aggregated results",
)
def test_batch_query_success() -> None:
    """Batch query returns aggregated results."""
    return


@scenario(
    "../features/api_batch_query.feature",
    "Pagination and partial failures",
)
def test_batch_query_pagination_partial() -> None:
    """Batch query handles pagination with partial failures."""
    return


@scenario(
    "../features/api_batch_query.feature",
    "Error recovery when a subquery fails",
)
def test_batch_query_error_recovery() -> None:
    """Batch query recovers from individual subquery failure."""
    return


@when("I submit a batch query with mixed reasoning modes")
def submit_batch_mixed_modes(
    test_context: BehaviorContext,
    dummy_query_response: QueryResponse,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Submit a batch query where each subquery uses a different reasoning mode."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    def run_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        *_: object,
        **__: object,
    ) -> dict[str, Any]:
        payload = as_payload(dummy_query_response.model_dump())
        payload["answer"] = query
        mode = getattr(config, "reasoning_mode", None)
        if mode is not None:
            metrics = cast(dict[str, Any], payload.setdefault("metrics", {}))
            metrics["mode"] = getattr(mode, "value", mode)
        return payload

    monkeypatch.setattr(Orchestrator, "run_query", run_query)

    payload = as_payload(
        {
            "queries": [
                {"query": "q1", "reasoning_mode": "direct"},
                {"query": "q2", "reasoning_mode": "dialectical"},
                {"query": "q3", "reasoning_mode": "chain-of-thought"},
            ]
        }
    )
    client = test_context["client"]
    resp = client.post("/query/batch?page=1&page_size=3", json=payload)
    test_context["response"] = resp
    test_context["queries"] = ["q1", "q2", "q3"]
    test_context["modes"] = ["direct", "dialectical", "chain-of-thought"]


@then("I receive aggregated results for each subquery")
def check_aggregated_results(test_context: BehaviorContext) -> None:
    resp = test_context["response"]
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["results"]) == 3
    assert all("error" not in r for r in data["results"])
    store_payload(test_context, "data", data)


@then("the results maintain submission order")
def check_ordering(test_context: BehaviorContext) -> None:
    data = test_context["data"]
    answers = [r["answer"] for r in data["results"]]
    assert answers == test_context["queries"]


@then("each subquery's response records its reasoning mode")
def check_modes(test_context: BehaviorContext) -> None:
    data = test_context["data"]
    modes = [r["metrics"].get("mode") for r in data["results"]]
    assert modes == test_context["modes"]


@when("I submit a paginated batch query where one subquery fails")
def submit_paginated_with_failure(
    test_context: BehaviorContext,
    dummy_query_response: QueryResponse,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Submit a batch query with pagination where a subquery errors."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    def run_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        *_: object,
        **__: object,
    ) -> dict[str, Any]:
        if query == "q3":
            raise ValueError("boom")
        payload = as_payload(dummy_query_response.model_dump())
        payload["answer"] = query
        return payload

    monkeypatch.setattr(Orchestrator, "run_query", run_query)

    payload = as_payload(
        {
            "queries": [
                {"query": "q1"},
                {"query": "q2"},
                {"query": "q3"},
                {"query": "q4"},
            ]
        }
    )
    client = test_context["client"]
    resp = client.post("/query/batch?page=2&page_size=2", json=payload)
    test_context["response"] = resp


@then("I receive the requested page with results and errors preserved")
def check_paginated_results(test_context: BehaviorContext) -> None:
    resp = test_context["response"]
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert len(data["results"]) == 2
    first, second = data["results"]
    assert first["answer"].startswith("Error")
    assert first["metrics"].get("error") == "boom"
    assert second["answer"] == "q4"
    assert "error" not in second["metrics"]
    store_payload(test_context, "data", data)


@then("failed subqueries include error details")
def check_error_details(test_context: BehaviorContext) -> None:
    data = test_context["data"]
    assert "error_details" in data["results"][0]["metrics"]


@when("I submit a batch query with a failing subquery followed by a valid one")
def submit_batch_error_recovery(
    test_context: BehaviorContext,
    dummy_query_response: QueryResponse,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Submit a batch query containing a failing subquery followed by a valid one."""

    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    def run_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        *_: object,
        **__: object,
    ) -> dict[str, Any]:
        if query == "bad":
            raise RuntimeError("fail")
        payload = as_payload(dummy_query_response.model_dump())
        payload["answer"] = query
        return payload

    monkeypatch.setattr(Orchestrator, "run_query", run_query)

    payload = as_payload(
        {"queries": [{"query": "good1"}, {"query": "bad"}, {"query": "good2"}]}
    )
    client = test_context["client"]
    resp = client.post("/query/batch", json=payload)
    test_context["response"] = resp


@then("processing continues and results include error for the failing subquery")
def check_error_recovery(test_context: BehaviorContext) -> None:
    resp = test_context["response"]
    assert resp.status_code == 200
    data = resp.json()
    answers = [r["answer"] for r in data["results"]]
    assert answers == ["good1", "Error: fail", "good2"]
    assert data["results"][1]["metrics"].get("error") == "fail"
    assert "error" not in data["results"][0]["metrics"]
    assert "error" not in data["results"][2]["metrics"]
