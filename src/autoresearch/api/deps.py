"""Common dependencies for Autoresearch API modules."""

from __future__ import annotations

from fastapi import Depends, Request
from fastapi.params import Depends as DependsDependency

from ..orchestration.orchestrator import Orchestrator
from .utils import enforce_permission


def require_permission(permission: str) -> DependsDependency:
    """Ensure the requesting client has a specific permission.

    Raises HTTP 401 with a ``WWW-Authenticate`` header when authentication
    information is missing and HTTP 403 when the user lacks the required
    permission.
    """

    async def checker(request: Request) -> None:
        permissions = getattr(request.state, "permissions", None)
        scheme = getattr(request.state, "www_authenticate", "API-Key")
        enforce_permission(permissions, permission, scheme)

    return Depends(checker)


def create_orchestrator() -> Orchestrator:
    """Create a new :class:`Orchestrator` instance."""
    return Orchestrator()
