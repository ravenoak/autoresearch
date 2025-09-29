from __future__ import annotations

from typing import Any, Protocol


class SupportsLoad(Protocol):
    def load(self, connection: Any) -> None: ...


def load(connection: Any) -> None: ...


__all__ = ["SupportsLoad", "load"]
