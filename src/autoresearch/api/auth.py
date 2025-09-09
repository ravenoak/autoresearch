"""Compatibility layer re-exporting API middlewares.

Historically authentication and rate limiting helpers lived under
``autoresearch.api.auth``.  The implementation now resides in
``autoresearch.api.middleware`` but imports from the old path are kept for
backward compatibility.
"""

from .middleware import (
    AuthMiddleware,
    FallbackRateLimitMiddleware,
    RateLimitMiddleware,
    dynamic_limit,
)

__all__ = [
    "AuthMiddleware",
    "FallbackRateLimitMiddleware",
    "RateLimitMiddleware",
    "dynamic_limit",
]
