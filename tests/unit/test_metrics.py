from __future__ import annotations

from collections.abc import Callable
from typing import Any

import duckdb
from pytest import MonkeyPatch

from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import metrics
from autoresearch.orchestration.orchestrator import Orchestrator


class DummyConn:
    def execute(self, *args: Any, **kwargs: Any) -> DummyConn:
        return self


def test_metrics_collection_and_endpoint(
    monkeypatch: MonkeyPatch, orchestrator: Orchestrator
) -> None:
    metrics.reset_metrics()
    monkeypatch.setattr(duckdb, "connect", lambda *a, **k: DummyConn())

    cfg: ConfigModel = ConfigModel.model_construct(api=APIConfig(api_keys={"secret": "admin"}))
    orch: Orchestrator = orchestrator

    def fake_run_query(
        query: str,
        config: ConfigModel,
        callbacks: Callable[..., None] | None = None,
        **kwargs: Any,
    ) -> QueryResponse:
        metrics.record_query()
        m = metrics.OrchestrationMetrics()
        m.record_tokens("agent", 5, 7)
        m.record_error("agent")
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(orch, "run_query", fake_run_query)

    import sys
    import types

    from autoresearch.api import deps

    monkeypatch.setattr(deps, "require_permission", lambda _perm: lambda: None)
    prom: types.SimpleNamespace = types.SimpleNamespace(
        CONTENT_TYPE_LATEST="text/plain",
        generate_latest=lambda: (
            f"autoresearch_queries_total {metrics.QUERY_COUNTER._value.get()}\n"
            f"autoresearch_tokens_in_total {metrics.TOKENS_IN_COUNTER._value.get()}\n"
        ).encode(),
    )
    monkeypatch.setitem(sys.modules, "prometheus_client", prom)
    from autoresearch.api.routing import metrics_endpoint

    # Record metrics directly
    fake_run_query("hi", cfg)

    import asyncio

    resp = asyncio.run(metrics_endpoint(None))
    assert resp.status_code == 200
    body = resp.body.decode()
    assert "autoresearch_queries_total" in body
    assert "autoresearch_tokens_in_total" in body


def test_reset_metrics_clears_counters() -> None:
    metrics.QUERY_COUNTER.inc()
    metrics.ERROR_COUNTER.inc()
    metrics.reset_metrics()
    assert metrics.QUERY_COUNTER._value.get() == 0
    assert metrics.ERROR_COUNTER._value.get() == 0
