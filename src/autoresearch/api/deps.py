"""Common dependencies for Autoresearch API modules."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from ..orchestration.orchestrator import Orchestrator


def require_permission(permission: str):
    """Ensure the requesting client has a specific permission.

    Raises HTTP 401 when no authentication information is present and
    HTTP 403 when the user lacks the required permission.
    """

    async def checker(request: Request) -> None:
        permissions = getattr(request.state, "permissions", None)
        if permissions is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        if permission not in permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    return Depends(checker)


def create_orchestrator() -> Orchestrator:
    """Create a new :class:`Orchestrator` instance."""
    return Orchestrator()
