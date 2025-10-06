# mypy: ignore-errors
from __future__ import annotations

import asyncio
from typing import cast

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from requests import Response as HTTPResponse

from autoresearch.api.utils import generate_bearer_token
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.types import CallbackMap
from tests.typing_helpers import QueryRunner


def _setup(monkeypatch: pytest.MonkeyPatch) -> ConfigModel:
    cfg = ConfigModel(api=APIConfig())
    ConfigLoader.reset_instance()

    def _load_config_stub(self: ConfigLoader) -> ConfigModel:
        return cfg

    def _run_query_stub(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        **kwargs: object,
    ) -> QueryResponse:
        return QueryResponse(
            query=query,
            answer="ok",
            citations=[],
            reasoning=[],
            metrics={},
        )

    run_query_stub: QueryRunner = _run_query_stub
    monkeypatch.setattr(ConfigLoader, "load_config", _load_config_stub)
    monkeypatch.setattr(Orchestrator, "run_query", run_query_stub)
    return cfg


def test_http_bearer_token(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    token = generate_bearer_token()
    cfg.api.bearer_token = token

    resp = cast(
        HTTPResponse,
        api_client.post(
            "/query", json={"query": "q"}, headers={"Authorization": f"Bearer {token}"}
        ),
    )
    assert resp.status_code == 200

    resp = cast(
        HTTPResponse,
        api_client.post(
            "/query", json={"query": "q"}, headers={"Authorization": "Bearer bad"}
        ),
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"


def test_role_assignments(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"adm": "admin"}
    token = generate_bearer_token()
    cfg.api.bearer_token = token

    @api_client.app.get("/whoami")
    async def whoami(request: Request) -> JSONResponse:
        return JSONResponse({"role": request.state.role})

    resp_key = cast(HTTPResponse, api_client.get("/whoami", headers={"X-API-Key": "adm"}))
    assert resp_key.status_code == 200
    assert resp_key.json() == {"role": "admin"}

    resp_token = cast(
        HTTPResponse,
        api_client.get("/whoami", headers={"Authorization": f"Bearer {token}"}),
    )
    assert resp_token.status_code == 200
    assert resp_token.json() == {"role": "user"}

    resp_bad = cast(
        HTTPResponse, api_client.get("/whoami", headers={"X-API-Key": "bad"})
    )
    assert resp_bad.status_code == 401
    assert resp_bad.json()["detail"] == "Invalid API key"

    resp_missing = cast(HTTPResponse, api_client.get("/whoami"))
    assert resp_missing.status_code == 401
    assert resp_missing.json()["detail"] == "Missing token"


def test_rate_limit(monkeypatch: pytest.MonkeyPatch, api_client: TestClient) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 1

    resp1 = cast(HTTPResponse, api_client.post("/query", json={"query": "q"}))
    assert resp1.status_code == 200
    resp2 = cast(HTTPResponse, api_client.post("/query", json={"query": "q"}))
    assert resp2.status_code == 429
    assert resp2.text == "rate limit exceeded"


def test_rate_limit_configurable(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 2

    assert api_client.post("/query", json={"query": "q"}).status_code == 200
    assert api_client.post("/query", json={"query": "q"}).status_code == 200
    assert api_client.post("/query", json={"query": "q"}).status_code == 429


def test_role_permissions(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"adm": "admin", "usr": "user"}
    cfg.api.role_permissions = {"admin": ["query"], "user": []}

    ok = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "adm"})
    assert ok.status_code == 200

    denied = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "usr"})
    assert denied.status_code == 403


def test_single_api_key(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"

    ok = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "secret"})
    assert ok.status_code == 200

    missing = cast(HTTPResponse, api_client.post("/query", json={"query": "q"}))
    assert missing.status_code == 401
    assert missing.json()["detail"] == "Missing API key"
    assert missing.headers["WWW-Authenticate"] == "API-Key"


def test_invalid_api_key(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"good": "user"}

    bad = cast(
        HTTPResponse,
        api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "bad"}),
    )
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid API key"
    assert bad.headers["WWW-Authenticate"] == "API-Key"


def test_api_key_or_token(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Either a valid API key or bearer token authenticates the request."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    token = generate_bearer_token()
    cfg.api.bearer_token = token

    ok_key = api_client.post("/query", json={"query": "q"}, headers={"X-API-Key": "secret"})
    assert ok_key.status_code == 200

    ok_token = api_client.post(
        "/query", json={"query": "q"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert ok_token.status_code == 200

    missing = cast(HTTPResponse, api_client.post("/query", json={"query": "q"}))
    assert missing.status_code == 401
    assert missing.json()["detail"] == "Missing token"


def test_invalid_api_key_with_valid_token(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Invalid API key causes rejection even when token is valid."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    token = generate_bearer_token()
    cfg.api.bearer_token = token
    resp = cast(
        HTTPResponse,
        api_client.post(
            "/query",
            json={"query": "q"},
            headers={"X-API-Key": "bad", "Authorization": f"Bearer {token}"},
        ),
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid API key"


def test_invalid_token_with_valid_api_key(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Invalid bearer token is rejected even with a valid API key."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    cfg.api.bearer_token = generate_bearer_token()
    resp = cast(
        HTTPResponse,
        api_client.post(
            "/query",
            json={"query": "q"},
            headers={"X-API-Key": "secret", "Authorization": "Bearer bad"},
        ),
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"


def test_query_status_and_cancel(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"adm": "admin"}
    cfg.api.role_permissions = {"admin": ["query"]}

    loop = asyncio.new_event_loop()
    future = loop.create_future()
    future.set_result(QueryResponse(answer="ok", citations=[], reasoning=[], metrics={}))
    api_client.app.state.async_tasks["abc"] = future

    status = api_client.get("/query/abc", headers={"X-API-Key": "adm"})
    assert status.status_code == 200

    future2 = loop.create_future()
    api_client.app.state.async_tasks["def"] = future2
    cancel = api_client.delete("/query/def", headers={"X-API-Key": "adm"})
    assert cancel.status_code == 200


def test_invalid_bearer_token(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Invalid bearer token should return 401."""
    cfg = _setup(monkeypatch)
    cfg.api.bearer_token = generate_bearer_token()
    resp = cast(
        HTTPResponse,
        api_client.post(
            "/query", json={"query": "q"}, headers={"Authorization": "Bearer wrong"}
        ),
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"
    assert resp.headers["WWW-Authenticate"] == "Bearer"


def test_missing_bearer_token(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Requests without a token are rejected."""
    cfg = _setup(monkeypatch)
    cfg.api.bearer_token = generate_bearer_token()
    resp = cast(HTTPResponse, api_client.post("/query", json={"query": "q"}))
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing token"
    assert resp.headers["WWW-Authenticate"] == "Bearer"


def test_permission_denied(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """API key lacking permission results in 403."""
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"u": "user"}
    cfg.api.role_permissions = {"user": ["query"]}
    resp = api_client.get("/metrics", headers={"X-API-Key": "u"})
    assert resp.status_code == 403


def test_docs_protected(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Documentation endpoints require authentication when configured."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"

    unauth = api_client.get("/docs")
    assert unauth.status_code == 401

    ok = api_client.get("/docs", headers={"X-API-Key": "secret"})
    assert ok.status_code == 200

    openapi = api_client.get("/openapi.json", headers={"X-API-Key": "secret"})
    assert openapi.status_code == 200


def test_invalid_key_and_token(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    """Both credentials invalid results in 401."""
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    cfg.api.bearer_token = generate_bearer_token()
    resp = api_client.post(
        "/query",
        json={"query": "q"},
        headers={"X-API-Key": "wrong", "Authorization": "Bearer bad"},
    )
    assert resp.status_code == 401


def test_query_status_permission_denied(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"u": "user"}
    cfg.api.role_permissions = {"user": []}
    api_client.app.state.async_tasks["id"] = asyncio.new_event_loop().create_future()
    resp = api_client.get("/query/id", headers={"X-API-Key": "u"})
    assert resp.status_code == 403


def test_cancel_query_permission_denied(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"u": "user"}
    cfg.api.role_permissions = {"user": []}
    api_client.app.state.async_tasks["id"] = asyncio.new_event_loop().create_future()
    resp = api_client.delete("/query/id", headers={"X-API-Key": "u"})
    assert resp.status_code == 403


def test_verify_bearer_token_reexport() -> None:
    """``verify_bearer_token`` remains available via ``api.auth``."""
    from autoresearch.api.auth import verify_bearer_token as exported

    token = generate_bearer_token()
    assert exported(token, token)
    assert not exported("bad", token)
