from typing import Any, Protocol, Type


class Store(Protocol):
    def open(self, *args: Any, **kwargs: Any) -> None: ...


def register(name: str, kind: Type[Any], module_path: str, class_name: str) -> None: ...


__all__ = ["Store", "register"]
