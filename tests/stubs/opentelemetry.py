"""Minimal stub for the :mod:`opentelemetry` package."""

import sys
import types

if "opentelemetry" not in sys.modules:
    otel = types.ModuleType("opentelemetry")

    trace_mod = types.ModuleType("trace")

    class _Tracer:
        def start_as_current_span(self, *_a, **_k):
            class _Span:
                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    return False

            return _Span()

    trace_mod.get_tracer = lambda name=None: _Tracer()
    trace_mod.set_tracer_provider = lambda provider: None
    otel.trace = trace_mod
    sys.modules["opentelemetry.trace"] = trace_mod

    sdk_mod = types.ModuleType("sdk")
    resources_mod = types.ModuleType("resources")
    resources_mod.SERVICE_NAME = "service.name"

    class Resource:
        @staticmethod
        def create(_data):
            return Resource()

    resources_mod.Resource = Resource
    sys.modules["opentelemetry.sdk"] = sdk_mod
    sys.modules["opentelemetry.sdk.resources"] = resources_mod

    trace_sdk_mod = types.ModuleType("trace")

    class TracerProvider:
        pass

    trace_sdk_mod.TracerProvider = TracerProvider
    sys.modules["opentelemetry.sdk.trace"] = trace_sdk_mod

    export_mod = types.ModuleType("export")

    class BatchSpanProcessor:
        def __init__(self, *a, **k):
            pass

    class ConsoleSpanExporter:
        def __init__(self, *a, **k):
            pass

    export_mod.BatchSpanProcessor = BatchSpanProcessor
    export_mod.ConsoleSpanExporter = ConsoleSpanExporter
    sys.modules["opentelemetry.sdk.trace.export"] = export_mod

    sys.modules["opentelemetry"] = otel
