from typing import Any, Type

class Counter:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class Histogram:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class Gauge:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class CollectorRegistry:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

REGISTRY: CollectorRegistry

def start_http_server(port: int, addr: str = "0.0.0.0") -> None: ...
