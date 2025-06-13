"""Simple OpenTelemetry tracing helpers."""

from __future__ import annotations

from typing import Optional

from opentelemetry import trace  # type: ignore[import]
from opentelemetry.sdk.resources import (  # type: ignore[import]
    SERVICE_NAME,
    Resource,
)
from opentelemetry.sdk.trace import (  # type: ignore[import]
    TracerProvider,
)
from opentelemetry.sdk.trace.export import (  # type: ignore[import]
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

_tracer_provider: Optional[TracerProvider] = None


def setup_tracing(enabled: bool) -> None:
    """Initialize the tracer provider if tracing is enabled."""
    global _tracer_provider
    if not enabled or _tracer_provider is not None:
        return

    resource = Resource.create({SERVICE_NAME: "autoresearch"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _tracer_provider = provider


def get_tracer(name: str = __name__):
    """Return a tracer from the global provider."""
    return trace.get_tracer(name)
