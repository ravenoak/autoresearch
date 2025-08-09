"""FastAPI app aggregator for Autoresearch."""

from __future__ import annotations

from . import routing
from .errors import handle_rate_limit

app = routing.app
SLOWAPI_STUB = routing.SLOWAPI_STUB
RateLimitExceeded = routing.RateLimitExceeded
reset_request_log = routing.reset_request_log
dynamic_limit = routing.dynamic_limit
config_loader = routing.config_loader
capabilities_endpoint = routing.capabilities_endpoint
get_remote_address = routing.get_remote_address
log_request = routing.log_request
limiter = routing.limiter
parse = routing.parse
query_endpoint = routing.query_endpoint

app.add_exception_handler(RateLimitExceeded, handle_rate_limit)

__all__ = [
    "app",
    "SLOWAPI_STUB",
    "reset_request_log",
    "dynamic_limit",
    "config_loader",
    "capabilities_endpoint",
    "get_remote_address",
    "log_request",
    "REQUEST_LOG",
    "REQUEST_LOG_LOCK",
    "limiter",
    "parse",
    "query_endpoint",
]


def __getattr__(name: str):
    if name == "REQUEST_LOG":
        return routing.REQUEST_LOG
    if name == "REQUEST_LOG_LOCK":
        return routing.REQUEST_LOG_LOCK
    raise AttributeError(name)
