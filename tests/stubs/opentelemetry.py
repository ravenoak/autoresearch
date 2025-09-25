"""Typed stub for :mod:`opentelemetry` used in tests."""

from __future__ import annotations

from types import ModuleType
from typing import Any, Literal, Protocol, cast

from ._registry import install_stub_module


class _Span:
    def __enter__(self) -> _Span:
        return self

    def __exit__(self, *exc: Any) -> Literal[False]:
        return False


class _Tracer:
    def start_as_current_span(self, *_args: Any, **_kwargs: Any) -> _Span:
        return _Span()


class TraceModule(Protocol):
    def get_tracer(self, name: str | None = None) -> _Tracer: ...

    def set_tracer_provider(self, provider: Any) -> None: ...


class _TraceModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("opentelemetry.trace")

    def get_tracer(self, name: str | None = None) -> _Tracer:
        return _Tracer()

    def set_tracer_provider(self, provider: Any) -> None:
        return None


class Resource:
    @staticmethod
    def create(_data: Any) -> Resource:
        return Resource()


class ResourcesModule(Protocol):
    SERVICE_NAME: str
    Resource: type[Resource]


class _ResourcesModule(ModuleType):
    SERVICE_NAME = "service.name"
    Resource = Resource

    def __init__(self) -> None:
        super().__init__("opentelemetry.sdk.resources")


class TracerProvider:
    pass


class SDKTraceModule(Protocol):
    TracerProvider: type[TracerProvider]


class _SDKTraceModule(ModuleType):
    TracerProvider = TracerProvider

    def __init__(self) -> None:
        super().__init__("opentelemetry.sdk.trace")


class BatchSpanProcessor:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        return None


class ConsoleSpanExporter:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        return None


class SDKTraceExportModule(Protocol):
    BatchSpanProcessor: type[BatchSpanProcessor]
    ConsoleSpanExporter: type[ConsoleSpanExporter]


class _SDKTraceExportModule(ModuleType):
    BatchSpanProcessor = BatchSpanProcessor
    ConsoleSpanExporter = ConsoleSpanExporter

    def __init__(self) -> None:
        super().__init__("opentelemetry.sdk.trace.export")


class SDKModule(Protocol):
    resources: ResourcesModule
    trace: SDKTraceModule


class _SDKModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("opentelemetry.sdk")
        self.resources = cast(
            ResourcesModule,
            install_stub_module("opentelemetry.sdk.resources", _ResourcesModule),
        )
        self.trace = cast(
            SDKTraceModule,
            install_stub_module("opentelemetry.sdk.trace", _SDKTraceModule),
        )
        install_stub_module("opentelemetry.sdk.trace.export", _SDKTraceExportModule)


class OpenTelemetryModule(Protocol):
    trace: TraceModule
    sdk: SDKModule


class _OpenTelemetryModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("opentelemetry")
        self.trace = cast(TraceModule, install_stub_module("opentelemetry.trace", _TraceModule))
        self.sdk = cast(SDKModule, install_stub_module("opentelemetry.sdk", _SDKModule))


opentelemetry = cast(
    OpenTelemetryModule, install_stub_module("opentelemetry", _OpenTelemetryModule)
)

__all__ = [
    "BatchSpanProcessor",
    "ConsoleSpanExporter",
    "OpenTelemetryModule",
    "Resource",
    "ResourcesModule",
    "SDKModule",
    "SDKTraceExportModule",
    "SDKTraceModule",
    "TraceModule",
    "TracerProvider",
    "opentelemetry",
]
