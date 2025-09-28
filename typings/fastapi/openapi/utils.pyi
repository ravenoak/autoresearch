from typing import Any


def get_openapi(*, title: str, version: str, routes: list[Any]) -> dict[str, Any]: ...


__all__ = ["get_openapi"]
