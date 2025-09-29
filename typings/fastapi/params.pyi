from __future__ import annotations

from typing import Any, Callable


class Depends:
    def __init__(
        self,
        dependency: Callable[..., Any] | None = ...,
        *,
        use_cache: bool = ...,
    ) -> None: ...


__all__ = ["Depends"]
