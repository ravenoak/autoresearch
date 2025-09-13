"""Integration tests for versioned query endpoint."""

from autoresearch.api.models import QueryResponseV1
from autoresearch.config import APIConfig, ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator


def _setup(monkeypatch) -> None:
    cfg = ConfigModel(api=APIConfig())
    ConfigLoader.reset_instance()
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)


def test_query_returns_version(monkeypatch, api_client) -> None:
    """The standard query endpoint returns a versioned response."""
    _setup(monkeypatch)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda self, q, c, callbacks=None, **k: QueryResponseV1(
            answer=q, citations=[], reasoning=[], metrics={}
        ),
    )
    resp = api_client.post("/query", json={"query": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1"
    assert body["answer"] == "hello"
