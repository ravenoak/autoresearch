# Tracing

OpenTelemetry instrumentation in Autoresearch provides distributed tracing to
debug and analyze performance. The tracing helpers configure a global tracer
provider with a console exporter by default.

## Setup

Add `autoresearch.tracing.setup_tracing` at application start. The helper
creates a tracer provider and registers a batch span processor with a console
exporter. For custom exporters, replace the processor before calling any
spans. Refer to [OpenTelemetry Python docs][otel-python].

[otel-python]: https://opentelemetry.io/docs/instrumentation/python/

## Context propagation

Tracing uses context variables to link spans across function calls and
threads. Each span created with `start_as_current_span` becomes the parent for
nested spans. When using asynchronous tasks or background threads, inject the
current context with `opentelemetry.propagate`. This ensures trace continuity
when work crosses process or network boundaries.

## Failure modes

- Tracing disabled: calling `setup_tracing(False)` leaves the no-op provider
  active, so span creation has minimal cost.
- Exporter failure: if the exporter cannot reach its endpoint, spans are
  dropped after the retry buffer fills.
- Context loss: forgetting to propagate context across async or thread
  boundaries breaks span linkage and produces orphaned traces.

## Simulation

Automated tests confirm tracing behavior.

- [Spec](../specs/tracing.md)
- [Tests](../../tests/behavior/features/tracing.feature)
