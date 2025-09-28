from typing import Any, Awaitable, Callable, Mapping

Scope = Mapping[str, Any]
Receive = Callable[[], Awaitable[Any]]
Send = Callable[[dict[str, Any]], Awaitable[Any]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[Any]]

__all__ = ["ASGIApp", "Receive", "Scope", "Send"]
