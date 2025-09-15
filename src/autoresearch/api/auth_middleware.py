"""Authentication middleware for the Autoresearch API."""

from __future__ import annotations

import secrets
from typing import cast

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from ..config import ConfigLoader
from .utils import verify_bearer_token


class AuthMiddleware:
    """API key and token authentication middleware."""

    def __init__(self, app: ASGIApp):
        """Initialize the middleware.

        Args:
            app: Downstream ASGI application.
        """

        self.app = app

    @staticmethod
    def _unauthorized(detail: str, scheme: str) -> JSONResponse:
        """Return a 401 response with ``WWW-Authenticate`` header.

        Args:
            detail: Human readable error message.
            scheme: Authentication scheme for the ``WWW-Authenticate`` header
                (e.g. ``"API-Key"`` or ``"Bearer"``).

        Returns:
            JSON response object representing the error.
        """

        return JSONResponse(
            {"detail": detail},
            status_code=401,
            headers={"WWW-Authenticate": scheme},
        )

    def _resolve_role(self, key: str | None, cfg) -> tuple[str, JSONResponse | None]:
        """Return the role for ``key`` or an error response.

        Args:
            key: Provided API key or ``None``.
            cfg: Loaded API configuration.

        Returns:
            A tuple containing the resolved role and an optional error response.
        """

        if cfg.api_keys:
            if not key:
                return "anonymous", self._unauthorized("Missing API key", "API-Key")
            for candidate, role in cfg.api_keys.items():
                if secrets.compare_digest(candidate, key):
                    return role, None
            return "anonymous", self._unauthorized("Invalid API key", "API-Key")

        if cfg.api_key:
            if not key:
                return "anonymous", self._unauthorized("Missing API key", "API-Key")
            if not secrets.compare_digest(key, cfg.api_key):
                return "anonymous", self._unauthorized("Invalid API key", "API-Key")
            return "user", None

        return "anonymous", None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Authenticate requests using API keys or bearer tokens."""

        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        app_state = scope["app"].state  # type: ignore[index]
        loader = cast(ConfigLoader, app_state.config_loader)
        loader._config = loader.load_config()
        cfg = loader._config.api

        auth_scheme = "API-Key" if (cfg.api_keys or cfg.api_key) else "Bearer"

        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        api_key = headers.get(b"x-api-key")
        auth_header = headers.get(b"authorization")

        key_valid = False
        role = "anonymous"
        if api_key is not None:
            api_key_str = api_key.decode()
            role, key_error = self._resolve_role(api_key_str, cfg)
            if key_error:
                await key_error(scope, receive, send)
                return
            key_valid = True

        token_valid = False
        if (auth_header or not key_valid) and cfg.bearer_token:
            token = None
            if auth_header:
                auth_str = auth_header.decode()
                if auth_str.lower().startswith("bearer "):
                    token = auth_str.split(" ", 1)[1]
            token_valid = verify_bearer_token(token, cfg.bearer_token)
            if token and not token_valid:
                resp = self._unauthorized("Invalid token", "Bearer")
                await resp(scope, receive, send)
                return

        auth_configured = bool(cfg.api_keys or cfg.api_key or cfg.bearer_token)
        if auth_configured and not (key_valid or token_valid):
            if cfg.bearer_token and not key_valid:
                resp = self._unauthorized("Missing token", "Bearer")
            else:
                resp = self._unauthorized("Missing API key", "API-Key")
            await resp(scope, receive, send)
            return

        if not key_valid and token_valid:
            role = "user"
            auth_scheme = "Bearer"
        elif key_valid:
            auth_scheme = "API-Key"
        else:
            auth_scheme = "Bearer" if cfg.bearer_token else "API-Key"

        state = scope.setdefault("state", {})
        state["role"] = role
        state["permissions"] = set(cfg.role_permissions.get(role, []))
        state["www_authenticate"] = auth_scheme

        await self.app(scope, receive, send)


__all__ = ["AuthMiddleware"]
