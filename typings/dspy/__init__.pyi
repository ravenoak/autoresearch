from __future__ import annotations

from typing import Any

__all__ = ["__version__", "__getattr__"]

__version__: str


def __getattr__(name: str) -> Any: ...
