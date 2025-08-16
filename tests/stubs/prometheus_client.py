"""Minimal stub for the :mod:`prometheus_client` package."""

import sys
import types

if "prometheus_client" not in sys.modules:
    prom_stub = types.ModuleType("prometheus_client")

    class Counter:
        def __init__(self, *args, **kwargs):
            pass

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

    class CollectorRegistry:
        def __init__(self, *args, **kwargs):
            pass

    def start_http_server(*args, **kwargs):
        pass

    REGISTRY = CollectorRegistry()

    prom_stub.Counter = Counter
    prom_stub.Histogram = Histogram
    prom_stub.Gauge = Gauge
    prom_stub.CollectorRegistry = CollectorRegistry
    prom_stub.REGISTRY = REGISTRY
    prom_stub.start_http_server = start_http_server
    sys.modules["prometheus_client"] = prom_stub
