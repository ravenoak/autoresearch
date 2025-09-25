"""Typed stubs for the optional :mod:`a2a` SDK."""

from __future__ import annotations

from types import ModuleType
from typing import Any, Protocol, cast

from pydantic import BaseModel

from ._registry import install_stub_module


class Message(BaseModel):
    content: str = ""
    metadata: dict[str, Any] | None = None
    role: str = "agent"


class MessageSendParams(BaseModel):
    """Placeholder request parameters."""


class SendMessageRequest(BaseModel):
    message: Message | None = None


class SendMessageResponse(BaseModel):
    message: Message | None = None


class A2AClient:
    """Stub client that raises on any dynamic attribute access."""

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - defensive stub
        if name.startswith("__"):
            raise AttributeError(name)
        raise ImportError("A2A SDK not installed")


def new_agent_text_message(
    content: str = "", metadata: dict[str, Any] | None = None
) -> Message:
    return Message(content=content, metadata=metadata or {})


def get_message_text(message: Message) -> str:
    return message.content


class A2AClientModule(Protocol):
    A2AClient: type[A2AClient]

    def __getattr__(self, name: str) -> Any: ...


class A2AUtilsModule(Protocol):
    message: "A2AUtilsMessageModule"


class A2AUtilsMessageModule(Protocol):
    def new_agent_text_message(
        self, content: str = "", metadata: dict[str, Any] | None = None
    ) -> Message: ...

    def get_message_text(self, message: Message) -> str: ...


class A2ATypesModule(Protocol):
    Message: type[Message]
    MessageSendParams: type[MessageSendParams]
    SendMessageRequest: type[SendMessageRequest]
    SendMessageResponse: type[SendMessageResponse]


class A2AModule(Protocol):
    client: A2AClientModule
    utils: A2AUtilsModule
    types: A2ATypesModule


class _A2AClientModule(ModuleType):
    A2AClient = A2AClient

    def __init__(self) -> None:
        super().__init__("a2a.client")

    def __getattr__(self, name: str) -> Any:
        return getattr(A2AClient(), name)


class _A2AUtilsModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("a2a.utils")


class _A2AUtilsMessageModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("a2a.utils.message")

    def new_agent_text_message(
        self, content: str = "", metadata: dict[str, Any] | None = None
    ) -> Message:
        return new_agent_text_message(content, metadata)

    def get_message_text(self, message: Message) -> str:
        return get_message_text(message)


class _A2ATypesModule(ModuleType):
    Message = Message
    MessageSendParams = MessageSendParams
    SendMessageRequest = SendMessageRequest
    SendMessageResponse = SendMessageResponse

    def __init__(self) -> None:
        super().__init__("a2a.types")


class _A2AStub(ModuleType):
    def __init__(self) -> None:
        super().__init__("a2a")


a2a = cast(A2AModule, install_stub_module("a2a", _A2AStub))
a2a_client = cast(A2AClientModule, install_stub_module("a2a.client", _A2AClientModule))
a2a_utils = cast(A2AUtilsModule, install_stub_module("a2a.utils", _A2AUtilsModule))
a2a_utils_message = cast(
    A2AUtilsMessageModule, install_stub_module("a2a.utils.message", _A2AUtilsMessageModule)
)
a2a_types = cast(A2ATypesModule, install_stub_module("a2a.types", _A2ATypesModule))

setattr(a2a_utils, "message", a2a_utils_message)
setattr(a2a, "client", a2a_client)
setattr(a2a, "utils", a2a_utils)
setattr(a2a, "types", a2a_types)


__all__ = [
    "A2AClient",
    "Message",
    "MessageSendParams",
    "SendMessageRequest",
    "SendMessageResponse",
    "a2a",
    "a2a_client",
    "a2a_utils",
    "a2a_utils_message",
    "a2a_types",
    "get_message_text",
    "new_agent_text_message",
]
