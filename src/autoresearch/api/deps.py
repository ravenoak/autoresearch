"""Common dependencies for Autoresearch API modules."""

from __future__ import annotations

from fastapi import Depends, Request

from ..orchestration.orchestrator import Orchestrator
from .utils import enforce_permission


def require_permission(permission: str):
    """Ensure the requesting client has a specific permission.

    Raises HTTP 401 when no authentication information is present and
    HTTP 403 when the user lacks the required permission.
    """

    async def checker(request: Request) -> None:
        permissions = getattr(request.state, "permissions", None)
        enforce_permission(permissions, permission)

    return Depends(checker)


def create_orchestrator() -> Orchestrator:
    """Create a new :class:`Orchestrator` instance."""
    return Orchestrator()
