"""OpenTelemetry tracing helpers for performance monitoring and debugging.

This module provides a simple interface to OpenTelemetry tracing functionality,
allowing the application to create and manage traces for performance monitoring
and debugging. Traces provide a way to track the flow of requests through the
system, measure execution times, and identify bottlenecks.

The module uses a global tracer provider that can be enabled or disabled through
configuration. When enabled, it outputs trace spans to the console, which can be
redirected to a file or captured by a monitoring system.

Typical usage:
    ```python
    from autoresearch.tracing import setup_tracing, get_tracer

    # Enable tracing at application startup
    setup_tracing(enabled=True)

    # Get a tracer for a specific component
    tracer = get_tracer("my_component")

    # Create and use spans to track operations
    with tracer.start_as_current_span("operation_name") as span:
        # Perform the operation
        result = perform_operation()

        # Add attributes to the span for context
        span.set_attribute("result_size", len(result))
    ```

The tracing system is designed to have minimal overhead when disabled, making it
safe to include tracing calls throughout the codebase without significant
performance impact in production environments where tracing might be disabled.
"""

from __future__ import annotations

from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import (
    SERVICE_NAME,
    Resource,
)
from opentelemetry.sdk.trace import (
    TracerProvider,
)
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

_tracer_provider: Optional[TracerProvider] = None


def setup_tracing(enabled: bool) -> None:
    """Initialize the global tracer provider if tracing is enabled.

    This function sets up the OpenTelemetry tracing infrastructure if it hasn't
    been initialized yet and if tracing is enabled. It creates a tracer provider
    with a console exporter that outputs trace spans to the console.

    The function is idempotent - calling it multiple times with the same parameters
    will only initialize the tracer provider once. This makes it safe to call
    from multiple entry points in the application.

    Args:
        enabled (bool): Whether tracing should be enabled. If False, this function
            does nothing and any tracing calls will have minimal overhead.

    Returns:
        None

    Note:
        The tracer provider is stored in a global variable to ensure it remains
        active for the lifetime of the application. The provider is configured with
        a batch span processor that buffers spans and exports them periodically,
        reducing the overhead of tracing.
    """
    global _tracer_provider
    if not enabled or _tracer_provider is not None:
        return

    resource = Resource.create({SERVICE_NAME: "autoresearch"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _tracer_provider = provider


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Get a tracer instance from the global tracer provider.

    This function returns a tracer instance that can be used to create spans
    for tracing operations. The tracer is associated with the specified name,
    which helps identify the source of spans in the tracing output.

    If tracing is not enabled (setup_tracing was called with enabled=False or
    not called at all), this function still returns a valid tracer, but any
    spans created by it will be no-ops with minimal overhead.

    Args:
        name (str, optional): The name to associate with the tracer, typically
            the module name or component name. Defaults to the calling module's name.

    Returns:
        trace.Tracer: A tracer instance that can be used to create spans.

    Example:
        ```python
        tracer = get_tracer("search_component")
        with tracer.start_as_current_span("perform_search") as span:
            results = search_database(query)
            span.set_attribute("result_count", len(results))
        ```
    """
    return trace.get_tracer(name)
