from pytest_bdd import given, when, then, scenario

from . import common_steps  # noqa: F401
from autoresearch import tracing
from typing import Any

from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult


class MemorySpanExporter(SpanExporter):
    """Collect spans in memory for verification."""

    def __init__(self) -> None:
        self._spans: list[Any] = []

    def export(self, spans):  # type: ignore[override]
        self._spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # type: ignore[override]
        self._spans.clear()

    def get_finished_spans(self):
        return list(self._spans)


@given("tracing is enabled")
def enable_tracing(test_context, monkeypatch):
    exporter = MemorySpanExporter()
    monkeypatch.setattr(tracing, "ConsoleSpanExporter", lambda: exporter)
    monkeypatch.setattr(tracing, "BatchSpanProcessor", SimpleSpanProcessor)
    tracing.setup_tracing(True)
    test_context["exporter"] = exporter
    test_context["tracer"] = tracing.get_tracer("bdd")


@given("tracing is disabled")
def disable_tracing(test_context, monkeypatch):
    exporter = MemorySpanExporter()
    monkeypatch.setattr(tracing, "ConsoleSpanExporter", lambda: exporter)
    monkeypatch.setattr(tracing, "BatchSpanProcessor", SimpleSpanProcessor)
    tracing.setup_tracing(False)
    test_context["exporter"] = exporter
    test_context["tracer"] = tracing.get_tracer("bdd")


@when("I perform a traced operation")
def perform_traced_operation(test_context):
    tracer = test_context["tracer"]
    with tracer.start_as_current_span("test-span") as span:
        span.set_attribute("foo", "bar")


@then('a span is recorded with name "test-span" and attribute "foo"="bar"')
def assert_span_recorded(test_context):
    exporter = test_context["exporter"]
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "test-span"
    assert span.attributes.get("foo") == "bar"


@then("no spans are recorded")
def assert_no_spans(test_context):
    exporter = test_context["exporter"]
    spans = exporter.get_finished_spans()
    assert spans == []


@scenario("../features/tracing.feature", "Tracing enabled emits spans")
def test_tracing_enabled():
    pass


@scenario("../features/tracing.feature", "Tracing disabled emits no spans")
def test_tracing_disabled():
    pass
