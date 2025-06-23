import responses
from fastapi.testclient import TestClient

from autoresearch.api import app as api_app
from autoresearch.config import ConfigModel, ConfigLoader, APIConfig
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState


def test_query_stream_param(monkeypatch):
    """/query should stream when stream=true is passed."""

    def dummy_run_query(query, config, callbacks=None, **kwargs):
        state = QueryState(query=query)
        for i in range(2):
            if callbacks and "on_cycle_end" in callbacks:
                callbacks["on_cycle_end"](i, state)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    cfg = ConfigModel(loops=2, api=APIConfig())
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    client = TestClient(api_app)

    with client.stream("POST", "/query?stream=true", json={"query": "q"}) as resp:
        assert resp.status_code == 200
        chunks = [line for line in resp.iter_lines()]
    assert len(chunks) == 3


def test_config_webhooks(monkeypatch):
    """Configured webhooks should receive final results."""

    cfg = ConfigModel(api=APIConfig(webhooks=["http://hook"], webhook_timeout=1))
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(answer="ok", citations=[], reasoning=[], metrics={}),
    )
    client = TestClient(api_app)

    with responses.RequestsMock() as rsps:
        rsps.post("http://hook", status=200)
        resp = client.post("/query", json={"query": "hi"})
        assert resp.status_code == 200
        assert len(rsps.calls) == 1
