import pytest

from autoresearch.api.utils import generate_bearer_token
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState

from .test_api_auth import _setup


def _setup_stream(monkeypatch):
    cfg = _setup(monkeypatch)

    def dummy_run_query(query, config, callbacks=None, **kwargs):
        state = QueryState(query=query)
        if callbacks and "on_cycle_end" in callbacks:
            callbacks["on_cycle_end"](0, state)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    return cfg


@pytest.mark.slow
def test_streaming_with_api_key(monkeypatch, api_client):
    cfg = _setup_stream(monkeypatch)
    cfg.api.api_key = "secret"

    with api_client.stream(
        "POST", "/query?stream=true", json={"query": "q"}, headers={"X-API-Key": "secret"}
    ) as resp:
        assert resp.status_code == 200
        _ = [line for line in resp.iter_lines()]

    bad = api_client.post("/query?stream=true", json={"query": "q"}, headers={"X-API-Key": "bad"})
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid API key"
    assert bad.headers["WWW-Authenticate"] == "API-Key"

    missing = api_client.post("/query?stream=true", json={"query": "q"})
    assert missing.status_code == 401
    assert missing.json()["detail"] == "Missing API key"
    assert missing.headers["WWW-Authenticate"] == "API-Key"


@pytest.mark.slow
def test_streaming_forbidden(monkeypatch, api_client):
    cfg = _setup_stream(monkeypatch)
    cfg.api.api_keys = {"usr": "user"}
    cfg.api.role_permissions = {"user": []}
    resp = api_client.post(
        "/query?stream=true",
        json={"query": "q"},
        headers={"X-API-Key": "usr"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Insufficient permissions"


@pytest.mark.slow
def test_streaming_with_bearer_token(monkeypatch, api_client):
    cfg = _setup_stream(monkeypatch)
    token = generate_bearer_token()
    cfg.api.bearer_token = token

    with api_client.stream(
        "POST",
        "/query?stream=true",
        json={"query": "q"},
        headers={"Authorization": f"Bearer {token}"},
    ) as resp:
        assert resp.status_code == 200
        _ = [line for line in resp.iter_lines()]

    bad = api_client.post(
        "/query?stream=true",
        json={"query": "q"},
        headers={"Authorization": "Bearer bad"},
    )
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid token"
    assert bad.headers["WWW-Authenticate"] == "Bearer"

    missing = api_client.post("/query?stream=true", json={"query": "q"})
    assert missing.status_code == 401
    assert missing.json()["detail"] == "Missing token"
    assert missing.headers["WWW-Authenticate"] == "Bearer"
