import asyncio
from types import SimpleNamespace

from fastapi import Request
from starlette.responses import Response

from autoresearch.api.middleware import AuthMiddleware
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel


def test_resolve_role_valid_key():
    cfg = ConfigModel(api=APIConfig(api_keys={"good": "user"}))
    middleware = AuthMiddleware(lambda *_: None)
    role, err = middleware._resolve_role("good", cfg.api)
    assert role == "user"
    assert err is None


def test_resolve_role_invalid_key():
    cfg = ConfigModel(api=APIConfig(api_keys={"good": "user"}))
    middleware = AuthMiddleware(lambda *_: None)
    role, err = middleware._resolve_role("bad", cfg.api)
    assert role == "anonymous"
    assert err is not None
    # Invalid keys now return 401 Unauthorized
    assert err.status_code == 401


def test_resolve_role_missing_key():
    cfg = ConfigModel(api=APIConfig(api_keys={"good": "user"}))
    middleware = AuthMiddleware(lambda *_: None)
    role, err = middleware._resolve_role(None, cfg.api)
    assert role == "anonymous"
    assert err is not None
    assert err.status_code == 401


def test_dispatch_invalid_token(monkeypatch):
    cfg = ConfigModel(api=APIConfig(bearer_token="secret"))
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    app = SimpleNamespace(state=SimpleNamespace(config_loader=ConfigLoader()))
    scope = {
        "type": "http",
        "path": "/",
        "method": "GET",
        "headers": [(b"authorization", b"Bearer bad")],
        "app": app,
    }
    request = Request(scope)
    middleware = AuthMiddleware(lambda *_: None)

    async def call_next(_):
        return Response("ok")

    resp = asyncio.run(middleware.dispatch(request, call_next))
    # Invalid bearer tokens yield 401 responses
    assert resp.status_code == 401
