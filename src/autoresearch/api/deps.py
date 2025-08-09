"""Common dependencies for Autoresearch API modules."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request


def require_permission(permission: str):
    """Ensure the requesting client has a specific permission."""

    async def checker(request: Request) -> None:
        permissions: set[str] = getattr(request.state, "permissions", set())
        if permission not in permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    return Depends(checker)
