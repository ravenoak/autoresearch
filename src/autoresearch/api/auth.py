"""Compatibility shim for legacy authentication helpers.

Historically ``AuthMiddleware`` and ``verify_bearer_token`` lived in
``autoresearch.api.auth``. They now reside in :mod:`autoresearch.api.auth_middleware`
and :mod:`autoresearch.api.utils` respectively. This module re-exports these
symbols so older imports remain valid. ``AuthMiddleware`` validates API keys and
roles before request bodies are read.
"""

from .auth_middleware import AuthMiddleware
from .utils import verify_bearer_token

__all__ = ["AuthMiddleware", "verify_bearer_token"]
