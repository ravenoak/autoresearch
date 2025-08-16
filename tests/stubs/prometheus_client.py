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

    prom_stub.Counter = Counter
    prom_stub.Histogram = Histogram
    sys.modules["prometheus_client"] = prom_stub
