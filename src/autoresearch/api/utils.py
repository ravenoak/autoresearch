from __future__ import annotations

import secrets
import threading
from collections import Counter
from typing import cast

from fastapi import FastAPI


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


def verify_bearer_token(token: str, expected: str) -> bool:
    """Validate a bearer token using constant-time comparison.

    Args:
        token: Token supplied by the client.
        expected: Reference token from configuration.

    Returns:
        ``True`` if the tokens match, ``False`` otherwise.
    """

    return secrets.compare_digest(token, expected)
