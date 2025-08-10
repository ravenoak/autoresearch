"""FastAPI app aggregator for Autoresearch."""

from __future__ import annotations

from . import routing

create_app = routing.create_app
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

__all__ = [
    "app",
    "create_app",
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
