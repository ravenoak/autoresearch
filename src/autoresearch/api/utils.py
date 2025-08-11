from __future__ import annotations

from collections import Counter
import threading
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
            return self._log[ip]

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._log)


def create_request_logger() -> RequestLogger:
    """Factory for creating a new :class:`RequestLogger` instance."""
    return RequestLogger()


def get_request_logger(app: FastAPI | None = None) -> RequestLogger:
    """Retrieve the application's request logger."""
    if app is None:
        app = cast(FastAPI | None, globals().get("app"))
        if app is None:
            return create_request_logger()
    return cast(RequestLogger, app.state.request_logger)


def reset_request_log(app: FastAPI | None = None) -> None:
    """Clear the application's request log."""
    get_request_logger(app).reset()
