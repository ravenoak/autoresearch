"""Typed stub for :mod:`prometheus_client` used in the test suite."""

from __future__ import annotations

from types import ModuleType
from typing import Any, ClassVar, Protocol, cast

from ._registry import install_stub_module


class _Metric:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - trivial
        return None


class Counter(_Metric):
    """Stub Counter metric."""


class Histogram(_Metric):
    """Stub Histogram metric."""


class Gauge(_Metric):
    """Stub Gauge metric."""


class CollectorRegistry:
    """Stub CollectorRegistry that records no state."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - trivial
        return None


def _start_http_server_stub(port: int, addr: str = "0.0.0.0") -> None:
    """Mimic :func:`prometheus_client.start_http_server` without networking."""


def start_http_server(port: int, addr: str = "0.0.0.0") -> None:
    _start_http_server_stub(port, addr)


class PrometheusClientModule(Protocol):
    Counter: ClassVar[type[Counter]]
    Histogram: ClassVar[type[Histogram]]
    Gauge: ClassVar[type[Gauge]]
    CollectorRegistry: ClassVar[type[CollectorRegistry]]
    REGISTRY: ClassVar[CollectorRegistry]

    def start_http_server(self, port: int, addr: str = "0.0.0.0") -> None: ...


class _PrometheusClientModule(ModuleType):
    Counter: ClassVar[type[Counter]] = Counter
    Histogram: ClassVar[type[Histogram]] = Histogram
    Gauge: ClassVar[type[Gauge]] = Gauge
    CollectorRegistry: ClassVar[type[CollectorRegistry]] = CollectorRegistry
    REGISTRY: ClassVar[CollectorRegistry] = CollectorRegistry()

    def __init__(self) -> None:
        super().__init__("prometheus_client")

    def start_http_server(self, port: int, addr: str = "0.0.0.0") -> None:
        _start_http_server_stub(port, addr)


prometheus_client = cast(
    PrometheusClientModule, install_stub_module("prometheus_client", _PrometheusClientModule)
)

__all__ = [
    "Counter",
    "CollectorRegistry",
    "Gauge",
    "Histogram",
    "prometheus_client",
    "PrometheusClientModule",
    "start_http_server",
]
