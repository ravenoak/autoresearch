import importlib

import duckdb
from fastapi.testclient import TestClient

from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration import metrics


class DummyConn:
    def execute(self, *args, **kwargs):
        return self


def test_metrics_collection_and_endpoint(monkeypatch):
    monkeypatch.setattr(duckdb, "connect", lambda *a, **k: DummyConn())

    cfg = ConfigModel.model_construct(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["metrics"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader.reset_instance()

    api = importlib.import_module("autoresearch.api")
    app = api.app
    start_queries = metrics.QUERY_COUNTER._value.get()
    start_errors = metrics.ERROR_COUNTER._value.get()

    m = metrics.OrchestrationMetrics()
    metrics.record_query()
    m.record_tokens("agent", 5, 7)
    m.record_error("agent")

    assert metrics.QUERY_COUNTER._value.get() == start_queries + 1
    assert metrics.ERROR_COUNTER._value.get() == start_errors + 1
    assert metrics.TOKENS_IN_COUNTER._value.get() >= 5
    assert metrics.TOKENS_OUT_COUNTER._value.get() >= 7

    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "autoresearch_queries_total" in body
    assert "autoresearch_tokens_in_total" in body
