from autoresearch import tracing
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    InMemorySpanExporter,
    SimpleSpanProcessor,
)


def test_setup_tracing_idempotent():
    tracing._tracer_provider = None
    tracing.setup_tracing(True)
    first = tracing._tracer_provider
    tracing.setup_tracing(True)
    assert tracing._tracer_provider is first
    assert tracing.get_tracer("t")
    if tracing._tracer_provider:
        tracing._tracer_provider.shutdown()
    tracing._tracer_provider = None


def test_setup_tracing_disabled():
    tracing._tracer_provider = None
    tracing.setup_tracing(False)
    assert tracing._tracer_provider is None


def test_span_export(monkeypatch):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    prev_provider = trace.get_tracer_provider()
    trace._TRACER_PROVIDER = provider
    monkeypatch.setattr(tracing, "_tracer_provider", provider, raising=False)
    try:
        tracer = tracing.get_tracer("demo")
        with tracer.start_as_current_span("demo-span"):
            pass
        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "demo-span"
    finally:
        provider.shutdown()
        trace._TRACER_PROVIDER = prev_provider
