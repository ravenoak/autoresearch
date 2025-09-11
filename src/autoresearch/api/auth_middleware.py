"""Authentication middleware for the Autoresearch API."""

from __future__ import annotations

import secrets
from typing import cast

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import ConfigLoader
from .utils import verify_bearer_token

security = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """API key and token authentication middleware."""

    @staticmethod
    def _unauthorized(detail: str, scheme: str) -> JSONResponse:
        """Return a 401 response with ``WWW-Authenticate`` header.

        Args:
            detail: Human readable error message.
            scheme: Authentication scheme for the ``WWW-Authenticate`` header
                (e.g. ``"API-Key"`` or ``"Bearer"``).
        """

        return JSONResponse(
            {"detail": detail},
            status_code=401,
            headers={"WWW-Authenticate": scheme},
        )

    def _resolve_role(self, key: str | None, cfg) -> tuple[str, JSONResponse | None]:
        """Return the role for ``key`` or an error response."""

        if cfg.api_keys:
            match_role: str | None = None
            if key:
                for candidate, role in cfg.api_keys.items():
                    if secrets.compare_digest(candidate, key):
                        match_role = role
            if match_role:
                return match_role, None
            if key:
                return "anonymous", self._unauthorized("Invalid API key", "API-Key")
            return "anonymous", None
        if cfg.api_key:
            if not (key and secrets.compare_digest(key, cfg.api_key)):
                if key:
                    return "anonymous", self._unauthorized("Invalid API key", "API-Key")
                return "anonymous", None
            return "user", None
        return "anonymous", None

    async def dispatch(self, request: Request, call_next):
        """Authenticate requests using API keys or bearer tokens."""

        loader = cast(ConfigLoader, request.app.state.config_loader)
        loader._config = loader.load_config()
        cfg = loader._config.api

        api_key = request.headers.get("X-API-Key")
        credentials: HTTPAuthorizationCredentials | None = await security(request)
        token = credentials.credentials if credentials else None

        key_role, key_error = self._resolve_role(api_key, cfg)
        provided_key = bool(api_key)
        if provided_key and key_error:
            return key_error
        key_valid = provided_key and key_error is None

        token_valid = verify_bearer_token(token, cfg.bearer_token)
        provided_token = bool(token)
        if provided_token and not token_valid:
            return self._unauthorized("Invalid token", "Bearer")

        if key_valid:
            role = key_role
        elif token_valid:
            role = "user"
        else:
            role = "anonymous"

        request.state.role = role
        request.state.permissions = set(cfg.role_permissions.get(role, []))

        auth_configured = bool(cfg.api_keys or cfg.api_key or cfg.bearer_token)
        if auth_configured and not (key_valid or token_valid):
            if (cfg.api_keys or cfg.api_key) and cfg.bearer_token:
                return self._unauthorized("Missing API key or token", "API-Key")
            if cfg.api_keys or cfg.api_key:
                return self._unauthorized("Missing API key", "API-Key")
            return self._unauthorized("Missing token", "Bearer")

        return await call_next(request)


__all__ = ["AuthMiddleware"]
