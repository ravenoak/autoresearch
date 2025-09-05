"""Compatibility shim exposing the API router.

The router and endpoint functions live in :mod:`autoresearch.api.routing`.
Importing from ``autoresearch.api.routes`` remains supported for backward
compatibility.
"""

from .routing import router

__all__ = ["router"]
