# mypy: ignore-errors
"""Integration coverage for typed middleware state interactions."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from autoresearch.api.middleware import SLOWAPI_STUB
from autoresearch.api.utils import generate_bearer_token
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


def _configure_api(monkeypatch) -> ConfigModel:
    cfg = ConfigModel(api=APIConfig())
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda *_a, **_k: QueryResponse(answer="ok", citations=[], reasoning=[], metrics={}),
    )
    return cfg


def test_rate_limit_state_captures_client(monkeypatch, api_client):
    cfg = _configure_api(monkeypatch)
    cfg.api.rate_limit = 1
    captured: dict[str, Any] = {}

    @api_client.app.get("/diagnostics/rate-limit")
    async def capture_rate_limit(request: Request):
        captured["value"] = getattr(request.state, "view_rate_limit", None)
        return JSONResponse({"ok": True})

    response = api_client.get("/diagnostics/rate-limit")
    assert response.status_code == 200

    view_rate_limit = captured["value"]
    assert isinstance(view_rate_limit, tuple)
    limit_obj, identifiers = view_rate_limit
    assert isinstance(identifiers, list)
    assert identifiers and all(isinstance(identifier, str) for identifier in identifiers)
    if not SLOWAPI_STUB:
        assert hasattr(limit_obj, "amount")
    else:
        assert limit_obj is not None


def test_auth_state_exposes_role_and_permissions(monkeypatch, api_client):
    cfg = _configure_api(monkeypatch)
    cfg.api.api_keys = {"adm": "admin"}
    cfg.api.role_permissions = {"admin": ["query", "docs"], "user": ["query"]}
    token = generate_bearer_token()
    cfg.api.bearer_token = token

    @api_client.app.get("/diagnostics/auth")
    async def capture_auth_state(request: Request):
        permissions = getattr(request.state, "permissions", None)
        scheme = getattr(request.state, "www_authenticate", None)
        role = getattr(request.state, "role", None)
        return JSONResponse(
            {
                "permissions": sorted(permissions) if permissions else None,
                "scheme": scheme,
                "role": role,
            }
        )

    resp_key = api_client.get("/diagnostics/auth", headers={"X-API-Key": "adm"})
    assert resp_key.status_code == 200
    assert resp_key.json() == {
        "permissions": ["docs", "query"],
        "scheme": "API-Key",
        "role": "admin",
    }

    resp_token = api_client.get(
        "/diagnostics/auth",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_token.status_code == 200
    assert resp_token.json() == {
        "permissions": ["query"],
        "scheme": "Bearer",
        "role": "user",
    }
