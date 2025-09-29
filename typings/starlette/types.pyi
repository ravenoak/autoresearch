from typing import Any, Awaitable, Callable, MutableMapping

Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Any]]
Send = Callable[[dict[str, Any]], Awaitable[Any]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[Any]]

__all__ = ["ASGIApp", "Receive", "Scope", "Send"]
