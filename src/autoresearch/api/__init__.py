"""FastAPI app aggregator for Autoresearch."""

from __future__ import annotations

from . import routing
from .auth_middleware import AuthMiddleware as _AuthMiddleware
from .errors import handle_rate_limit as _handle_rate_limit
from .middleware import (
    SLOWAPI_STUB,
    FallbackRateLimitMiddleware as _FallbackRateLimitMiddleware,
    RateLimitMiddleware as _RateLimitMiddleware,
)
from .middleware import Limiter as _Limiter
from .middleware import RateLimitExceeded as _RateLimitExceeded
from .middleware import (
    dynamic_limit,
    get_remote_address,
    parse as _parse,
)
from .models import (
    AsyncQueryResponseV1,
    BatchQueryRequestV1,
    BatchQueryResponseV1,
    QueryRequestV1,
    QueryResponseV1,
)
from .streaming import query_stream_endpoint
from .utils import (
    RequestLogger,
    create_request_logger,
    enforce_permission,
    get_request_logger,
    reset_request_log,
)

create_app = routing.create_app
app = routing.app
config_loader = routing.config_loader
capabilities_endpoint = routing.capabilities_endpoint
limiter = routing.limiter
query_endpoint = routing.query_endpoint
RateLimitExceeded = _RateLimitExceeded
Limiter = _Limiter
parse = _parse
FallbackRateLimitMiddleware = _FallbackRateLimitMiddleware
RateLimitMiddleware = _RateLimitMiddleware
AuthMiddleware = _AuthMiddleware
handle_rate_limit = _handle_rate_limit

__all__ = [
    "app",
    "create_app",
    "SLOWAPI_STUB",
    "dynamic_limit",
    "config_loader",
    "capabilities_endpoint",
    "get_remote_address",
    "limiter",
    "RateLimitExceeded",
    "Limiter",
    "query_endpoint",
    "query_stream_endpoint",
    "QueryRequestV1",
    "QueryResponseV1",
    "BatchQueryRequestV1",
    "BatchQueryResponseV1",
    "AsyncQueryResponseV1",
    "enforce_permission",
    "create_request_logger",
    "get_request_logger",
    "RequestLogger",
    "reset_request_log",
    "parse",
    "FallbackRateLimitMiddleware",
    "RateLimitMiddleware",
    "AuthMiddleware",
    "handle_rate_limit",
]
