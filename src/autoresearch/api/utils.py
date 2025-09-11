from __future__ import annotations

import secrets
import threading
from collections import Counter
from typing import cast

from fastapi import FastAPI, HTTPException


class RequestLogger:
    """Thread-safe per-client request logger."""

    def __init__(self) -> None:
        self._log: Counter[str] = Counter()
        self._lock = threading.Lock()

    def log(self, ip: str) -> int:
        with self._lock:
            self._log[ip] += 1
            return self._log[ip]

    def reset(self) -> None:
        with self._lock:
            self._log.clear()

    def get(self, ip: str) -> int:
        with self._lock:
            return int(self._log.get(ip, 0))

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._log)


def create_request_logger() -> RequestLogger:
    """Factory for creating a new :class:`RequestLogger` instance."""
    return RequestLogger()


def get_request_logger(app: FastAPI | None = None) -> RequestLogger:
    """Retrieve the application's request logger.

    Raises:
        RuntimeError: If the request logger has not been initialised.
    """
    if app is None:
        try:
            from autoresearch import api as api_mod

            app = cast(FastAPI | None, getattr(api_mod, "app", None))
        except Exception:  # pragma: no cover - defensive
            app = None
        if app is None:
            raise RuntimeError("Request logger not initialised")

    logger = getattr(app.state, "request_logger", None)
    if logger is None:
        raise RuntimeError("Request logger not initialised")

    return cast(RequestLogger, logger)


def reset_request_log(app: FastAPI | None = None) -> None:
    """Clear the application's request log."""
    get_request_logger(app).reset()


def generate_bearer_token(length: int = 32) -> str:
    """Return a random URL-safe token.

    Args:
        length: Number of bytes of entropy for the token.

    Returns:
        Secure token suitable for use as a bearer credential.
    """

    return secrets.token_urlsafe(length)


def verify_bearer_token(token: str | None, expected: str | None) -> bool:
    """Validate a bearer token using constant-time comparison.

    Args:
        token: Token supplied by the client.
        expected: Reference token from configuration.

    Returns:
        ``True`` if both values are present and match, ``False`` otherwise.
    """

    if not (token and expected):
        return False
    return secrets.compare_digest(token, expected)


def enforce_permission(
    permissions: set[str] | None, required: str, auth_scheme: str = "API-Key"
) -> None:
    """Ensure a client has a specific permission.

    Args:
        permissions: Permissions granted to the client or ``None`` when
            authentication is missing.
        required: Permission required for the requested action.
        auth_scheme: Authentication scheme for the ``WWW-Authenticate`` header
            when ``permissions`` is ``None``.

    Raises:
        HTTPException: ``401`` if ``permissions`` is ``None`` and ``403`` when
            ``required`` is absent from ``permissions``.
    """

    if permissions is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": auth_scheme},
        )
    if required not in permissions:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


# Version support -----------------------------------------------------------

SUPPORTED_VERSIONS: set[str] = {"1"}
"""Set of recognised API schema versions."""

DEPRECATED_VERSIONS: set[str] = set()
"""Versions that remain parsable but return a ``410 Gone`` response."""


def validate_version(version: str) -> None:
    """Ensure an API version is supported and not deprecated.

    Args:
        version: Version string provided in the request body.

    Raises:
        HTTPException: ``410`` when the version is deprecated or ``400`` for
            unknown versions.
    """

    if version in DEPRECATED_VERSIONS:
        raise HTTPException(status_code=410, detail=f"API version {version} is deprecated")
    if version not in SUPPORTED_VERSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported API version {version}")
