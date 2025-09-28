from typing import Any, Mapping


class Response:
    status_code: int

    def __init__(
        self,
        content: Any = ...,
        status_code: int = ...,
        headers: Mapping[str, str] | None = ...,
        media_type: str | None = ...,
    ) -> None: ...


__all__ = ["Response"]
