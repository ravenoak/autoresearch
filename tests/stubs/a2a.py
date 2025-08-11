"""Stub for the optional :mod:`a2a` dependency."""

import sys
import types

if "a2a" not in sys.modules:
    a2a_stub = types.ModuleType("a2a")
    sys.modules["a2a"] = a2a_stub

    client_stub = types.ModuleType("a2a.client")

    class A2AClient:
        ...

    def _missing(name: str, *_a, **_k):
        if name.startswith("__"):
            raise AttributeError(name)
        raise ImportError("A2A SDK not installed")

    client_stub.A2AClient = A2AClient
    client_stub.__getattr__ = _missing
    client_stub.__file__ = __file__
    sys.modules["a2a.client"] = client_stub

    from typing import Any
    from pydantic import BaseModel

    utils_stub = types.ModuleType("a2a.utils")
    message_stub = types.ModuleType("a2a.utils.message")
    types_stub = types.ModuleType("a2a.types")

    class Message(BaseModel):
        content: str = ""
        metadata: dict[str, Any] | None = None
        role: str = "agent"

    def new_agent_text_message(content: str = "", metadata: dict[str, Any] | None = None) -> Message:
        return Message(content=content, metadata=metadata or {})

    def get_message_text(msg: Message) -> str:
        return msg.content

    message_stub.new_agent_text_message = new_agent_text_message
    message_stub.get_message_text = get_message_text
    sys.modules["a2a.utils"] = utils_stub
    sys.modules["a2a.utils.message"] = message_stub

    class MessageSendParams(BaseModel):
        ...

    class SendMessageRequest(BaseModel):
        message: Message | None = None

    class SendMessageResponse(BaseModel):
        message: Message | None = None

    types_stub.Message = Message
    types_stub.MessageSendParams = MessageSendParams
    types_stub.SendMessageRequest = SendMessageRequest
    types_stub.SendMessageResponse = SendMessageResponse
    sys.modules["a2a.types"] = types_stub
