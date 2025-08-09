"""FastAPI app aggregator for Autoresearch."""

from __future__ import annotations

from .routing import (
    app,
    SLOWAPI_STUB,
    RateLimitExceeded,
    reset_request_log,
    dynamic_limit,
    config_loader,
    capabilities_endpoint,
    get_remote_address,
    REQUEST_LOG,
    REQUEST_LOG_LOCK,
    limiter,
    parse,
)
from .errors import handle_rate_limit

app.add_exception_handler(RateLimitExceeded, handle_rate_limit)

__all__ = [
    "app",
    "SLOWAPI_STUB",
    "reset_request_log",
    "dynamic_limit",
    "config_loader",
    "capabilities_endpoint",
    "get_remote_address",
    "REQUEST_LOG",
    "REQUEST_LOG_LOCK",
    "limiter",
    "parse",
]
