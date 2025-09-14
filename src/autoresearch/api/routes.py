"""Compatibility shim exposing the API router.

This module re-exports the main router but omits the ``/metrics`` endpoint
unless monitoring is enabled in the configuration.
"""

from fastapi import APIRouter

from ..config import ConfigLoader
from .routing import router as _router


def _build_router() -> APIRouter:
    cfg = ConfigLoader().load_config().api
    if cfg.monitoring_enabled:
        return _router
    router = APIRouter()
    for route in _router.routes:
        if route.path != "/metrics":
            router.routes.append(route)
    return router


router = _build_router()

__all__ = ["router"]
