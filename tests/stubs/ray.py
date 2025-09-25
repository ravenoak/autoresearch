"""Typed stub for :mod:`ray`."""

from __future__ import annotations

import importlib.util
from types import ModuleType, SimpleNamespace
from typing import Any, Callable, Protocol, cast

from ._registry import install_stub_module


def _remote(func: Callable[..., Any]) -> SimpleNamespace:
    return SimpleNamespace(remote=lambda *args, **kwargs: func(*args, **kwargs))


def _noop(*_args: Any, **_kwargs: Any) -> None:
    return None


def _identity(value: Any) -> Any:
    return value


class RayCompiledDagNodeModule(Protocol):
    def _shutdown_all_compiled_dags(self) -> None: ...


class RayDagModule(Protocol):
    compiled_dag_node: RayCompiledDagNodeModule


class RayModule(Protocol):
    dag: RayDagModule

    def init(self, *args: Any, **kwargs: Any) -> None: ...

    def shutdown(self, *args: Any, **kwargs: Any) -> None: ...

    def remote(self, func: Callable[..., Any]) -> SimpleNamespace: ...

    def get(self, value: Any) -> Any: ...

    def put(self, value: Any) -> Any: ...

    ObjectRef: type


class _RayModule(ModuleType):
    ObjectRef = object

    def __init__(self) -> None:
        super().__init__("ray")
        self.dag = cast(RayDagModule, install_stub_module("ray.dag", _RayDagModule))

    def init(self, *args: Any, **kwargs: Any) -> None:
        _noop(*args, **kwargs)

    def shutdown(self, *args: Any, **kwargs: Any) -> None:
        _noop(*args, **kwargs)

    def remote(self, func: Callable[..., Any]) -> SimpleNamespace:
        return _remote(func)

    def get(self, value: Any) -> Any:
        return _identity(value)

    def put(self, value: Any) -> Any:
        return _identity(value)


class _RayDagModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("ray.dag")
        self.compiled_dag_node = cast(
            RayCompiledDagNodeModule,
            install_stub_module("ray.dag.compiled_dag_node", _RayCompiledDagNodeModule),
        )


class _RayCompiledDagNodeModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("ray.dag.compiled_dag_node")

    def _shutdown_all_compiled_dags(self) -> None:
        return None


if importlib.util.find_spec("ray") is None:
    ray = cast(RayModule, install_stub_module("ray", _RayModule))
else:  # pragma: no cover
    import ray as _ray

    ray = cast(RayModule, _ray)


__all__ = ["RayModule", "ray"]
