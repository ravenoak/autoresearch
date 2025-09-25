from __future__ import annotations

from typing import Any


def get_openapi(*, title: str, version: str, description: str, routes: Any) -> dict[str, Any]: ...

__all__ = ["get_openapi"]
