from __future__ import annotations

from typing import Any, Sequence

__all__ = [
    "figure",
    "plot",
    "savefig",
    "close",
    "tight_layout",
    "axis",
    "title",
]


def figure(*args: Any, **kwargs: Any) -> Any: ...


def plot(*args: Any, **kwargs: Any) -> Any: ...


def savefig(*args: Any, **kwargs: Any) -> None: ...


def close(*args: Any, **kwargs: Any) -> None: ...


def tight_layout() -> None: ...


def axis(option: str | Sequence[Any]) -> None: ...


def title(label: str, *args: Any, **kwargs: Any) -> None: ...
