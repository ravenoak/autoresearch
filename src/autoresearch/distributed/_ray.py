"""Typed helpers for interacting with Ray without requiring its stubs."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable, Generic, Mapping, Protocol, Sequence, TypeVar, cast

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
R = TypeVar("R")
R_co = TypeVar("R_co", covariant=True)


class RayObjectRef(Protocol[T_co]):
    """Typed handle for deferred results returned by Ray."""


class RemoteFunction(Protocol[R_co]):
    """Protocol for the callable returned by ``ray.remote``."""

    def remote(self, *args: Any, **kwargs: Any) -> RayObjectRef[R_co]:
        """Schedule a remote execution and return an object reference."""


class RayLike(Protocol):
    """Subset of Ray's public API consumed by the distributed executors."""

    ObjectRef: type

    def init(self, *args: Any, **kwargs: Any) -> Any:
        """Initialize the Ray runtime."""

    def shutdown(self) -> None:
        """Tear down the Ray runtime."""

    def is_initialized(self) -> bool:
        """Return whether Ray is currently initialized."""

    def put(self, value: T) -> RayObjectRef[T]:
        """Store ``value`` in the object store and return a reference."""

    def remote(self, func: Callable[..., R]) -> RemoteFunction[R]:
        """Decorate ``func`` for remote execution."""

    def get(self, ref: RayObjectRef[T] | Sequence[RayObjectRef[T]]) -> T | list[T]:
        ...


class RayQueueProtocol(Protocol):
    """Minimal queue interface used by :class:`RayBroker`."""

    def put(self, item: Mapping[str, Any]) -> None:
        ...

    def get(self, *, block: bool = True, timeout: float | None = None) -> dict[str, Any]:
        ...

    def shutdown(self) -> None:
        ...


class RayQueueFactory(Protocol):
    """Callable that constructs Ray queue instances."""

    def __call__(self, *args: Any, **kwargs: Any) -> RayQueueProtocol:
        ...


@dataclass
class _StubObjectRef(Generic[T]):
    value: T


class _LocalRemoteFunction(Generic[R]):
    """Synchronous drop-in replacement for ``ray.remote`` functions."""

    def __init__(self, func: Callable[..., R]) -> None:
        self._func = func

    def remote(self, *args: Any, **kwargs: Any) -> RayObjectRef[R]:
        return _StubObjectRef(self._func(*args, **kwargs))


class _RayStub:
    """Fallback runtime that mimics Ray when the package is unavailable."""

    ObjectRef: type = _StubObjectRef

    def init(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - trivial
        return None

    def shutdown(self) -> None:  # pragma: no cover - trivial
        return None

    def is_initialized(self) -> bool:  # pragma: no cover - trivial
        return True

    def put(self, value: T) -> RayObjectRef[T]:
        return _StubObjectRef(value)

    def get(self, ref: RayObjectRef[T] | Sequence[RayObjectRef[T]]) -> T | list[T]:
        if isinstance(ref, Sequence) and not isinstance(ref, (bytes, bytearray, str)):
            return [cast(_StubObjectRef[T], item).value for item in ref]
        return cast(_StubObjectRef[T], ref).value

    def remote(self, func: Callable[..., R]) -> RemoteFunction[R]:
        return _LocalRemoteFunction(func)


def optional_ray() -> RayLike:
    """Return Ray if installed, otherwise a lightweight synchronous stub."""

    try:
        module = importlib.import_module("ray")
    except Exception:  # pragma: no cover - exercised via stubbed runtime
        return _RayStub()
    return cast(RayLike, module)


def require_ray() -> RayLike:
    """Import Ray and provide a helpful message if it is missing."""

    try:
        module = importlib.import_module("ray")
    except ModuleNotFoundError as exc:  # pragma: no cover - import guard
        raise ModuleNotFoundError(
            "Ray is required for this distributed feature. Install it via the"
            " '[distributed]' extra."
        ) from exc
    return cast(RayLike, module)


def require_ray_queue() -> RayQueueFactory:
    """Return the Ray queue factory with consistent typing."""

    try:
        module = importlib.import_module("ray.util.queue")
    except ModuleNotFoundError as exc:  # pragma: no cover - import guard
        raise ModuleNotFoundError(
            "Ray queue support requires the 'ray' package. Install it via the"
            " '[distributed]' extra."
        ) from exc
    return cast(RayQueueFactory, getattr(module, "Queue"))

