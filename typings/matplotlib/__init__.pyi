from __future__ import annotations

from typing import Any

__all__ = ["use", "pyplot"]


def use(backend: str, *, force: bool | None = ...) -> None: ...


class _PyplotModule:
    def __getattr__(self, name: str) -> Any: ...


pyplot: _PyplotModule
