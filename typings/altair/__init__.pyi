from __future__ import annotations

from typing import Any

__all__ = ["Chart", "X", "Y", "Color", "value", "Scale", "condition", "datum"]


class Chart:
    def __init__(self, data: Any) -> None: ...

    def mark_bar(self, *args: Any, **kwargs: Any) -> Chart: ...

    def mark_line(self, *args: Any, **kwargs: Any) -> Chart: ...

    def encode(self, *args: Any, **kwargs: Any) -> Chart: ...

    def properties(self, *args: Any, **kwargs: Any) -> Chart: ...

    def __add__(self, other: Chart) -> Chart: ...


def X(field: str, *args: Any, **kwargs: Any) -> Any: ...


def Y(field: str, *args: Any, **kwargs: Any) -> Any: ...


def Color(field: str, *args: Any, **kwargs: Any) -> Any: ...


def value(val: Any) -> Any: ...


def Scale(*args: Any, **kwargs: Any) -> Any: ...


def condition(*args: Any, **kwargs: Any) -> Any: ...


datum: Any
