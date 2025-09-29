from typing import Any, Protocol


class BaseAdapter(Protocol):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def close(self) -> None: ...


class HTTPAdapter(BaseAdapter):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


__all__ = ["BaseAdapter", "HTTPAdapter"]
