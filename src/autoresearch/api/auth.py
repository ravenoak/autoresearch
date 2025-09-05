"""Compatibility shim for authentication middleware.

This module re-exports :class:`AuthMiddleware` so older imports targeting
``autoresearch.api.auth`` continue to function after the middleware was
relocated to :mod:`autoresearch.api.middleware`.
"""

from .middleware import AuthMiddleware

__all__ = ["AuthMiddleware"]
