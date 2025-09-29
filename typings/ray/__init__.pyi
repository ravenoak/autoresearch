from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Generic, Protocol, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class ObjectRef(Generic[T]):
    ...


class RemoteFunction(Generic[R], Protocol):
    def remote(self, *args: Any, **kwargs: Any) -> ObjectRef[R]: ...


def init(*args: Any, **kwargs: Any) -> None: ...

def shutdown() -> None: ...

def is_initialized() -> bool: ...

def put(value: T) -> ObjectRef[T]: ...

def get(ref: ObjectRef[T] | Sequence[ObjectRef[T]]) -> T | list[T]: ...

def remote(func: Callable[..., R]) -> RemoteFunction[R]: ...

def cluster_resources() -> dict[str, float]: ...


__all__ = [
    "ObjectRef",
    "RemoteFunction",
    "init",
    "shutdown",
    "is_initialized",
    "put",
    "get",
    "remote",
    "cluster_resources",
]
