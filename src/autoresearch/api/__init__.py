"""FastAPI app aggregator for Autoresearch."""

from __future__ import annotations

from . import routing
from .middleware import (
    SLOWAPI_STUB,
)
from .middleware import Limiter as _Limiter
from .middleware import RateLimitExceeded as _RateLimitExceeded
from .middleware import (
    dynamic_limit,
    get_remote_address,
    parse,
)
from .models import (
    AsyncQueryResponseV1,
    BatchQueryRequestV1,
    BatchQueryResponseV1,
    QueryRequestV1,
    QueryResponseV1,
)
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
    "RateLimitExceeded",
    "Limiter",
    "query_endpoint",
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
]
