import importlib

import duckdb
from fastapi.testclient import TestClient

from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.models import QueryResponse
from autoresearch.orchestration import metrics
from autoresearch.orchestration.orchestrator import Orchestrator


class DummyConn:
    def execute(self, *args, **kwargs):
        return self


def test_metrics_collection_and_endpoint(monkeypatch):
    monkeypatch.setattr(duckdb, "connect", lambda *a, **k: DummyConn())

    cfg = ConfigModel.model_construct(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query", "metrics"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader.reset_instance()
    orch = Orchestrator()

    def fake_run_query(query, config, callbacks=None, **kwargs):
        metrics.record_query()
        m = metrics.OrchestrationMetrics()
        m.record_tokens("agent", 5, 7)
        m.record_error("agent")
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(orch, "run_query", fake_run_query)
    import autoresearch.api.routing as routing
    import sys
    import types

    monkeypatch.setattr(routing, "create_orchestrator", lambda: orch)
    prom = types.SimpleNamespace(
        CONTENT_TYPE_LATEST="text/plain",
        generate_latest=lambda: (
            f"autoresearch_queries_total {metrics.QUERY_COUNTER._value.get()}\n"
            f"autoresearch_tokens_in_total {metrics.TOKENS_IN_COUNTER._value.get()}\n".encode()
        ),
    )
    monkeypatch.setitem(sys.modules, "prometheus_client", prom)

    api = importlib.import_module("autoresearch.api")
    app = api.app
    start_queries = (
        metrics.QUERY_COUNTER._value.get()
        if hasattr(metrics.QUERY_COUNTER, "_value")
        else 0
    )
    start_errors = (
        metrics.ERROR_COUNTER._value.get()
        if hasattr(metrics.ERROR_COUNTER, "_value")
        else 0
    )

    client = TestClient(app)
    client.post("/query", json={"query": "hi"})

    assert metrics.QUERY_COUNTER._value.get() == start_queries + 1
    assert metrics.ERROR_COUNTER._value.get() == start_errors + 1
    assert metrics.TOKENS_IN_COUNTER._value.get() >= 5
    assert metrics.TOKENS_OUT_COUNTER._value.get() >= 7

    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "autoresearch_queries_total" in body
    assert "autoresearch_tokens_in_total" in body
