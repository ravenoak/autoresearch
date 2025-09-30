import duckdb
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import metrics
import pytest
from typing import Any


class DummyConn:
    def execute(self, *args, **kwargs):
        return self


def test_metrics_collection_and_endpoint(monkeypatch: pytest.MonkeyPatch, orchestrator: Any) -> None:
    metrics.reset_metrics()
    monkeypatch.setattr(duckdb, "connect", lambda *a, **k: DummyConn())

    cfg = ConfigModel.model_construct(api=APIConfig(api_keys={"secret": "admin"}))
    orch = orchestrator

    def fake_run_query(query, config, callbacks=None, **kwargs):
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
    prom = types.SimpleNamespace(
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
