# mypy: ignore-errors
from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from requests import Response as HTTPResponse

from autoresearch.api.utils import generate_bearer_token
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.types import CallbackMap, CycleCallback
from tests.typing_helpers import QueryRunner

from .test_api_auth import _setup


def _setup_stream(monkeypatch: pytest.MonkeyPatch) -> ConfigModel:
    cfg = _setup(monkeypatch)

    def dummy_run_query(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        **kwargs: object,
    ) -> QueryResponse:
        state = QueryState(query=query)
        if callbacks and "on_cycle_end" in callbacks:
            on_cycle_end = cast(CycleCallback, callbacks["on_cycle_end"])
            on_cycle_end(0, state)
        return QueryResponse(
            query=query,
            answer="ok",
            citations=[],
            reasoning=[],
            metrics={},
        )

    run_query_stub: QueryRunner = dummy_run_query
    monkeypatch.setattr(Orchestrator, "run_query", run_query_stub)
    return cfg


@pytest.mark.slow
def test_streaming_with_api_key(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup_stream(monkeypatch)
    cfg.api.api_key = "secret"
    client = cast(Any, api_client)

    with client.stream(
        "POST", "/query?stream=true", json={"query": "q"}, headers={"X-API-Key": "secret"}
    ) as resp:
        response = cast(HTTPResponse, resp)
        assert response.status_code == 200
        response_lines = cast(Any, response)
        _ = [line for line in response_lines.iter_lines()]

    bad = cast(
        HTTPResponse,
        client.post("/query?stream=true", json={"query": "q"}, headers={"X-API-Key": "bad"}),
    )
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid API key"
    assert bad.headers["WWW-Authenticate"] == "API-Key"

    missing = cast(HTTPResponse, client.post("/query?stream=true", json={"query": "q"}))
    assert missing.status_code == 401
    assert missing.json()["detail"] == "Missing API key"
    assert missing.headers["WWW-Authenticate"] == "API-Key"


@pytest.mark.slow
def test_streaming_forbidden(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup_stream(monkeypatch)
    cfg.api.api_keys = {"usr": "user"}
    cfg.api.role_permissions = {"user": []}
    client = cast(Any, api_client)
    resp = cast(
        HTTPResponse,
        client.post(
            "/query?stream=true",
            json={"query": "q"},
            headers={"X-API-Key": "usr"},
        ),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Insufficient permissions"


@pytest.mark.slow
def test_streaming_with_bearer_token(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup_stream(monkeypatch)
    token = generate_bearer_token()
    cfg.api.bearer_token = token
    client = cast(Any, api_client)

    with client.stream(
        "POST",
        "/query?stream=true",
        json={"query": "q"},
        headers={"Authorization": f"Bearer {token}"},
    ) as resp:
        response = cast(HTTPResponse, resp)
        assert response.status_code == 200
        response_lines = cast(Any, response)
        _ = [line for line in response_lines.iter_lines()]

    bad = cast(
        HTTPResponse,
        client.post(
            "/query?stream=true",
            json={"query": "q"},
            headers={"Authorization": "Bearer bad"},
        ),
    )
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid token"
    assert bad.headers["WWW-Authenticate"] == "Bearer"

    missing = cast(HTTPResponse, client.post("/query?stream=true", json={"query": "q"}))
    assert missing.status_code == 401
    assert missing.json()["detail"] == "Missing token"
    assert missing.headers["WWW-Authenticate"] == "Bearer"
