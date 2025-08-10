"""FastAPI app aggregator for Autoresearch."""

from __future__ import annotations

from . import routing
from .errors import handle_rate_limit

app = routing.app
SLOWAPI_STUB = routing.SLOWAPI_STUB
RateLimitExceeded = routing.RateLimitExceeded
dynamic_limit = routing.dynamic_limit
config_loader = routing.config_loader
capabilities_endpoint = routing.capabilities_endpoint
get_remote_address = routing.get_remote_address
limiter = routing.limiter
parse = routing.parse
query_endpoint = routing.query_endpoint
create_request_logger = routing.create_request_logger
get_request_logger = routing.get_request_logger
RequestLogger = routing.RequestLogger
reset_request_log = routing.reset_request_log

app.add_exception_handler(RateLimitExceeded, handle_rate_limit)

__all__ = [
    "app",
    "SLOWAPI_STUB",
    "dynamic_limit",
    "config_loader",
    "capabilities_endpoint",
    "get_remote_address",
    "limiter",
    "parse",
    "query_endpoint",
    "create_request_logger",
    "get_request_logger",
    "RequestLogger",
    "reset_request_log",
]
