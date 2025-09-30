"""A2A (Agent-to-Agent) interface for Autoresearch.

This module provides integration with the A2A protocol, allowing Autoresearch
to be used as an agent in A2A-compatible systems. It implements the necessary
handlers and adapters to expose Autoresearch functionality through the A2A SDK.
"""

from __future__ import annotations

import asyncio
import os
import time
from enum import Enum
from functools import wraps
from threading import Thread
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Literal,
    Mapping,
    MutableMapping,
    Protocol,
    runtime_checkable,
    Self,
    TypedDict,
    cast,
    TypeVar,
)
from uuid import uuid4

import httpx
import uvicorn
from uvicorn.config import Config as UvicornConfig
from pydantic import BaseModel, ValidationError, ConfigDict

from .api import capabilities_endpoint
from .config import ConfigLoader, ConfigModel, get_config
from .error_utils import format_error_for_a2a, get_error_info
from .logging_utils import get_logger
from .orchestration.orchestrator import Orchestrator

logger = get_logger(__name__)

# Import ``pydantic.root_model`` early to avoid compatibility issues when the
# A2A SDK uses generics with Pydantic 2.
try:  # pragma: no cover - runtime import patch
    import sys

    import pydantic.root_model as _rm  # noqa: F401

    sys.modules.setdefault("pydantic.root_model", _rm)
except Exception:  # pragma: no cover - best effort
    pass

if TYPE_CHECKING:
    from a2a.client import A2AClient as SDKA2AClient
    from a2a.types import (
        Message,
        MessageSendParams,
        SendMessageRequest,
        SendMessageResponse,
    )
else:
    @runtime_checkable
    class Message(Protocol):
        """Structural type for messages exchanged with the A2A SDK."""

        metadata: Mapping[str, Any] | None

        @classmethod
        def model_validate(cls, data: Mapping[str, Any]) -> Self:
            ...

        def model_dump(self, *, mode: str = ...) -> dict[str, Any]:
            ...

    class MessageSendParams(Protocol):
        """Structural type describing message send parameters."""

        message: Message
        metadata: Mapping[str, Any] | None

        def __init__(self, *, message: Message, metadata: Mapping[str, Any] | None = ...) -> None:
            ...

    class SendMessageRequest(Protocol):
        """Structural type describing message send requests."""

        id: str
        params: MessageSendParams

        def __init__(self, *, id: str, params: MessageSendParams) -> None:
            ...

    class SendMessageResponse(Protocol):
        """Structural type for message responses from the A2A SDK."""

        def model_dump(self, *, mode: str = ...) -> dict[str, Any]:
            ...

    class SDKA2AClient(Protocol):
        """Structural type for the optional A2A client."""

        async def send_message(self, request: SendMessageRequest) -> SendMessageResponse:
            ...

A2A_AVAILABLE = False

_RuntimeA2AClient: type[Any] | None = None
_RuntimeMessage: type[Any] | None = None
_RuntimeMessageSendParams: type[Any] | None = None
_RuntimeSendMessageRequest: type[Any] | None = None
_RuntimeSendMessageResponse: type[Any] | None = None
_runtime_get_message_text: Callable[[Message], str] | None = None
_runtime_new_agent_text_message: Callable[..., Message] | None = None


class ASGIApplication(Protocol):
    """Structural ASGI callable type avoiding optional dependencies."""

    def __call__(
        self,
        scope: Mapping[str, Any],
        receive: Callable[..., Awaitable[Any]],
        send: Callable[..., Awaitable[Any]],
    ) -> Awaitable[None]:
        ...


class AgentInfo(TypedDict):
    """Summary of agent metadata surfaced via the info handler."""

    name: str
    version: str
    description: str
    capabilities: list[str]


class InfoResponse(TypedDict):
    """Response structure returned by ``_handle_info`` on success."""

    status: Literal["success"]
    agent_info: AgentInfo
    message: dict[str, Any]


try:  # pragma: no cover - optional dependency import
    from a2a.client import A2AClient as _ImportedA2AClient
    from a2a.types import (
        Message as _ImportedMessage,
        MessageSendParams as _ImportedMessageSendParams,
        SendMessageRequest as _ImportedSendMessageRequest,
        SendMessageResponse as _ImportedSendMessageResponse,
    )
    from a2a.utils.message import (
        get_message_text as _imported_get_message_text,
        new_agent_text_message as _imported_new_agent_text_message,
    )
except ImportError:  # pragma: no cover - dependency missing
    pass
else:
    _RuntimeA2AClient = cast("type[Any]", _ImportedA2AClient)
    _RuntimeMessage = cast("type[Any]", _ImportedMessage)
    _RuntimeMessageSendParams = cast("type[Any]", _ImportedMessageSendParams)
    _RuntimeSendMessageRequest = cast("type[Any]", _ImportedSendMessageRequest)
    _RuntimeSendMessageResponse = cast("type[Any]", _ImportedSendMessageResponse)
    _runtime_get_message_text = cast(
        Callable[[Message], str], _imported_get_message_text
    )
    _runtime_new_agent_text_message = cast(
        Callable[..., Message], _imported_new_agent_text_message
    )
    A2A_AVAILABLE = True


def _require_runtime_cls(name: str, value: type[Any] | None) -> type[Any]:
    if value is None:
        raise RuntimeError(f"A2A SDK is not available: missing {name} runtime class")
    return value


def _require_runtime_fn(name: str, func: Callable[..., Any] | None) -> Callable[..., Any]:
    if func is None:
        raise RuntimeError(f"A2A SDK is not available: missing {name} runtime helper")
    return func


def get_message_model_cls() -> type[Message]:
    """Return the runtime message class provided by the A2A SDK."""

    return cast("type[Message]", _require_runtime_cls("Message", _RuntimeMessage))


def get_message_send_params_cls() -> type[MessageSendParams]:
    """Return the runtime send-params class provided by the A2A SDK."""

    return cast(
        "type[MessageSendParams]",
        _require_runtime_cls("MessageSendParams", _RuntimeMessageSendParams),
    )


def get_send_message_request_cls() -> type[SendMessageRequest]:
    """Return the runtime send-message request class."""

    return cast(
        "type[SendMessageRequest]",
        _require_runtime_cls("SendMessageRequest", _RuntimeSendMessageRequest),
    )


def get_sdk_client_cls() -> type[SDKA2AClient]:
    """Return the runtime A2A client class."""

    return cast("type[SDKA2AClient]", _require_runtime_cls("SDKA2AClient", _RuntimeA2AClient))


def get_message_text(message: Message) -> str:
    """Proxy to the runtime ``get_message_text`` helper."""

    func = cast(Callable[[Message], str], _require_runtime_fn("get_message_text", _runtime_get_message_text))
    return func(message)


def new_agent_text_message(
    text: str,
    metadata: Mapping[str, Any] | None = None,
) -> Message:
    """Create a runtime message object using the SDK helper."""

    func = cast(
        Callable[[str, Mapping[str, Any] | None], Message],
        _require_runtime_fn("new_agent_text_message", _runtime_new_agent_text_message),
    )
    return func(text, metadata)


def create_message_send_params(
    *,
    message: Message,
    metadata: Mapping[str, Any] | None = None,
) -> MessageSendParams:
    """Instantiate ``MessageSendParams`` using the runtime class."""

    params_cls = get_message_send_params_cls()
    return params_cls(message=message, metadata=metadata)


def create_send_message_request(
    *,
    request_id: str,
    params: MessageSendParams,
) -> SendMessageRequest:
    """Instantiate ``SendMessageRequest`` using the runtime class."""

    request_cls = get_send_message_request_cls()
    return request_cls(id=request_id, params=params)


if A2A_AVAILABLE:
    class A2AMessageType(str, Enum):
        """Supported message types."""

        QUERY = "query"
        COMMAND = "command"
        INFO = "info"
        RESULT = "result"
        ERROR = "error"
        ACK = "ack"

    class A2AMessage(BaseModel):
        """Message wrapper used by the A2A interface."""

        model_config = ConfigDict(arbitrary_types_allowed=True)

        type: A2AMessageType
        message: Message

    MessageResponse = Mapping[str, Any]
    SyncMessageHandler = Callable[[Message], MessageResponse]
    AsyncMessageHandler = Callable[[Message], Awaitable[MessageResponse]]
    MessageHandler = SyncMessageHandler | AsyncMessageHandler

    class A2AServer:
        """FastAPI/uvicorn server for A2A messages."""

        def __init__(self, host: str, port: int) -> None:
            self.host = host
            self.port = port
            self._handlers: MutableMapping[str, MessageHandler] = {}
            self._server: uvicorn.Server | None = None
            self._thread: Thread | None = None

        def register_handler(
            self,
            message_type: str | A2AMessageType,
            handler: MessageHandler,
        ) -> None:
            """Register a handler for a given message type.

            The A2A SDK exposes message types as ``Enum`` members that inherit
            from ``str``. Calling :func:`str` on such a member yields the fully
            qualified name (e.g. ``"A2AMessageType.QUERY"``) rather than the raw
            value ``"query"`` supplied in HTTP payloads. To ensure dispatch can
            resolve handlers regardless of input form, both enum members and
            plain strings are normalised to their underlying string value before
            being stored.

            Args:
                message_type: Message type identifier or enum member.
                handler: Callable invoked for the given message type.
            """

            key = message_type.value if isinstance(message_type, Enum) else str(message_type)
            self._handlers[key] = handler

        async def _dispatch(self, msg_type: str, message_data: Mapping[str, Any]) -> dict[str, Any]:
            """Dispatch a request to the appropriate handler."""

            handler = self._handlers.get(msg_type)
            if handler is None:
                return {"status": "error", "error": "Unknown message type"}
            message_cls = get_message_model_cls()
            message = message_cls.model_validate(message_data)
            if asyncio.iscoroutinefunction(handler):
                async_handler = cast(AsyncMessageHandler, handler)
                response = await async_handler(message)
            else:
                sync_handler = cast(SyncMessageHandler, handler)
                response = await asyncio.to_thread(sync_handler, message)
            return dict(response)

        def start(self) -> None:
            """Start the HTTP server in a background thread."""

            from fastapi import FastAPI

            app = FastAPI()

            @app.post("/")
            async def handle(
                payload: Mapping[str, Any],
            ) -> dict[str, Any]:  # pragma: no cover - network
                msg_type = str(payload.get("type", ""))
                message_data = payload.get("message", {})
                return await self._dispatch(msg_type, message_data)

            asgi_app: ASGIApplication = cast(ASGIApplication, app)
            config = UvicornConfig(
                app=asgi_app,
                host=self.host,
                port=self.port,
                log_level="info",
            )
            server = uvicorn.Server(config)
            self._server = server

            def run() -> None:
                asyncio.run(server.serve())

            self._thread = Thread(target=run, daemon=True)
            self._thread.start()
            while not self._server.started:  # Wait for server to be ready
                time.sleep(0.01)

        def stop(self) -> None:
            """Stop the HTTP server."""

            if self._server:
                self._server.should_exit = True
            if self._thread:
                self._thread.join()


class A2AInterface:
    """Interface for integrating Autoresearch with A2A protocol."""

    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        """Initialize the A2A interface.

        Args:
            host: Optional host to bind the A2A server to. Falls back to the
                ``A2A_HOST`` environment variable or ``127.0.0.1``.
            port: Optional port to bind the A2A server to. Falls back to the
                ``A2A_PORT`` environment variable or ``8765``.

        Raises:
            ImportError: If the a2a-sdk package is not installed
        """
        if not A2A_AVAILABLE:
            raise ImportError(
                "The a2a-sdk package is required for A2A integration. "
                "Install it with: pip install a2a-sdk"
            )

        env_host = os.environ.get("A2A_HOST", "127.0.0.1")
        env_port = int(os.environ.get("A2A_PORT", "8765"))
        self.host = host or env_host
        self.port = port or env_port
        self.server = A2AServer(host=self.host, port=self.port)
        self.orchestrator = Orchestrator()

        # Register message handlers
        self.server.register_handler(A2AMessageType.QUERY, self._handle_query)
        self.server.register_handler(A2AMessageType.COMMAND, self._handle_command)
        self.server.register_handler(A2AMessageType.INFO, self._handle_info)

    def start(self) -> None:
        """Start the A2A server."""
        logger.info(f"Starting A2A server on {self.host}:{self.port}")
        self.server.start()

    def stop(self) -> None:
        """Stop the A2A server."""
        logger.info("Stopping A2A server")
        self.server.stop()

    async def _handle_query(self, message: Message) -> dict[str, Any]:
        """Handle a query message from another agent.

        Args:
            message: The incoming A2A message

        Returns:
            The response A2A message
        """
        query = ""
        if message.metadata:
            query = message.metadata.get("query", "")
        if not query:
            query = get_message_text(message)
        if not query:
            return {"status": "error", "error": "No query provided"}

        try:
            # Run the orchestrator query in a worker thread so multiple calls
            # can execute concurrently without blocking the event loop.
            result = await asyncio.to_thread(self.orchestrator.run_query, query, get_config())

            response_msg: Message = new_agent_text_message(result.answer)

            return {
                "status": "success",
                "message": response_msg.model_dump(mode="python"),
            }
        except Exception as e:
            # Get error information with suggestions and code examples
            error_info = get_error_info(e)
            error_data: dict[str, Any] = format_error_for_a2a(error_info)

            # Log the error
            logger.error(f"Error processing query: {e}", exc_info=e)

            # Return error response
            return error_data

    def _handle_command(self, message: Message) -> dict[str, Any]:
        """Handle a command message from another agent.

        Args:
            message: The incoming A2A message

        Returns:
            The response A2A message
        """
        command = ""
        args: dict[str, Any] = {}
        if message.metadata:
            command = message.metadata.get("command", "")
            metadata_args = message.metadata.get("args", {})
            if isinstance(metadata_args, dict):
                args = dict(metadata_args)
        if not command:
            command = get_message_text(message)

        if not command:
            return {"status": "error", "error": "No command provided"}

        # Handle different commands
        try:
            if command == "get_capabilities":
                result = self._handle_get_capabilities()
                return {"status": "success", "result": result}
            elif command == "get_config":
                result = self._handle_get_config()
                return {"status": "success", "result": result}
            elif command == "set_config":
                result = self._handle_set_config(args)
                return {"status": "success", "result": result}
            else:
                return {"status": "error", "error": f"Unknown command: {command}"}
        except Exception as e:
            # Get error information with suggestions and code examples
            error_info = get_error_info(e)
            error_data: dict[str, Any] = format_error_for_a2a(error_info)

            # Log the error
            logger.error(f"Error handling command {command}: {e}", exc_info=e)

            # Return error response
            return error_data

    def _handle_info(self, message: Message) -> InfoResponse | dict[str, Any]:
        """Handle an info message from another agent.

        Args:
            message: The incoming A2A message

        Returns:
            The response A2A message with agent information
        """
        try:
            # Get package version from the environment or use a default
            version = os.environ.get("AUTORESEARCH_VERSION", "0.1.0")

            agent_info: AgentInfo = {
                "name": "Autoresearch",
                "version": version,
                "description": "A local-first research assistant",
                "capabilities": [
                    "research",
                    "dialectical_reasoning",
                    "fact_checking",
                ],
            }

            info_msg: Message = new_agent_text_message("info")

            response: InfoResponse = {
                "status": "success",
                "agent_info": agent_info,
                "message": info_msg.model_dump(mode="python"),
            }
            return dict(response)
        except Exception as e:
            # Get error information with suggestions and code examples
            error_info = get_error_info(e)
            error_data: dict[str, Any] = format_error_for_a2a(error_info)

            # Log the error
            logger.error(f"Error handling info message: {e}", exc_info=e)

            # Return error response
            return error_data

    def _handle_get_capabilities(self) -> dict[str, Any]:
        """Handle a get_capabilities command.

        Returns:
            The capabilities information as a dictionary.
        """
        capabilities: dict[str, Any] = capabilities_endpoint()
        return capabilities

    def _handle_get_config(self) -> dict[str, Any]:
        """Handle a get_config command.

        Returns:
            The current configuration as a dictionary.
        """
        config = get_config()
        config_data: dict[str, Any] = config.model_dump(mode="python")
        return config_data

    def _handle_set_config(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle a set_config command.

        Args:
            args: The command arguments containing configuration updates

        Returns:
            The updated configuration as a dictionary or an error object.
        """
        loader = ConfigLoader()
        current = loader.config.model_dump(mode="python")
        current.update(args)
        try:
            new_config = ConfigModel(**current)
        except ValidationError as exc:
            error_info = get_error_info(exc)
            error_response: dict[str, Any] = format_error_for_a2a(error_info)
            return error_response

        loader._config = new_config
        loader.notify_observers(new_config)
        updated_config: dict[str, Any] = new_config.model_dump(mode="python")
        return updated_config


class A2AClientWrapper:
    """Client for connecting to other A2A-compatible agents."""

    def __init__(self) -> None:
        """Initialize the A2A client.

        Raises:
            ImportError: If the a2a-sdk package is not installed
        """
        if not A2A_AVAILABLE:
            raise ImportError(
                "The a2a-sdk package is required for A2A integration. "
                "Install it with: pip install a2a-sdk"
            )

        logger.info("A2A client initialized")

    def _send_request(self, agent_url: str, params: MessageSendParams) -> dict[str, Any]:
        """Send a message request and return the raw response as a dict."""

        async def _run() -> SendMessageResponse:
            async with httpx.AsyncClient() as http_client:
                client_cls = get_sdk_client_cls()
                client = client_cls(http_client, url=agent_url)
                request = create_send_message_request(
                    request_id=str(uuid4()),
                    params=params,
                )
                return await client.send_message(request)

        response = asyncio.run(_run())
        response_data: dict[str, Any] = response.model_dump(mode="python")
        return response_data

    def query_agent(self, agent_url: str, query: str) -> dict[str, Any]:
        """Send a query to another agent.

        Args:
            agent_url: The URL of the agent to query
            query: The query to send

        Returns:
            The response from the agent
        """
        try:
            params = create_message_send_params(
                message=new_agent_text_message(query)
            )
            response = self._send_request(agent_url, params)

            if "error" in response:
                logger.error(f"Error querying agent: {response.get('error')}")
                return {"error": response.get("error")}

            raw_result = response.get("result")
            if isinstance(raw_result, dict) and raw_result.get("kind") == "message" and raw_result.get("parts"):
                part = raw_result["parts"][0]
                if isinstance(part, dict) and "text" in part:
                    return {"answer": part["text"]}
            if isinstance(raw_result, dict):
                return raw_result
            if raw_result is not None:
                return {"result": raw_result}
            return {}
        except Exception as e:
            logger.error(f"Error querying agent: {e}")
            return {"error": str(e)}

    def get_agent_capabilities(self, agent_url: str) -> dict[str, Any]:
        """Get the capabilities of another agent.

        Args:
            agent_url: The URL of the agent

        Returns:
            The capabilities of the agent
        """
        try:
            params = create_message_send_params(
                message=new_agent_text_message("get_capabilities")
            )
            response = self._send_request(agent_url, params)

            if "error" in response:
                logger.error(f"Error getting agent capabilities: {response.get('error')}")
                return {"error": response.get("error")}

            raw_result = response.get("result")
            if isinstance(raw_result, dict):
                return raw_result
            if raw_result is not None:
                return {"result": raw_result}
            return {}
        except Exception as e:
            logger.error(f"Error getting agent capabilities: {e}")
            return {"error": str(e)}

    def get_agent_config(self, agent_url: str) -> dict[str, Any]:
        """Get the configuration of another agent.

        Args:
            agent_url: The URL of the agent

        Returns:
            The configuration of the agent
        """
        try:
            params = create_message_send_params(
                message=new_agent_text_message("get_config")
            )
            response = self._send_request(agent_url, params)

            if "error" in response:
                logger.error(f"Error getting agent config: {response.get('error')}")
                return {"error": response.get("error")}

            raw_result = response.get("result")
            if isinstance(raw_result, dict):
                return raw_result
            if raw_result is not None:
                return {"result": raw_result}
            return {}
        except Exception as e:
            logger.error(f"Error getting agent config: {e}")
            return {"error": str(e)}

    def set_agent_config(self, agent_url: str, config_updates: dict[str, Any]) -> dict[str, Any]:
        """Update the configuration of another agent.

        Args:
            agent_url: The URL of the agent
            config_updates: The configuration updates to apply

        Returns:
            The result of the configuration update
        """
        try:
            params = create_message_send_params(
                message=new_agent_text_message("set_config"),
                metadata={"args": config_updates},
            )
            response = self._send_request(agent_url, params)

            if "error" in response:
                logger.error(f"Error setting agent config: {response.get('error')}")
                return {"error": response.get("error")}

            raw_result = response.get("result")
            if isinstance(raw_result, dict):
                return raw_result
            if raw_result is not None:
                return {"result": raw_result}
            return {}
        except Exception as e:
            logger.error(f"Error setting agent config: {e}")
            return {"error": str(e)}


# Alias for backward compatibility
A2AClient = A2AClientWrapper  # noqa: F811


F = TypeVar("F", bound=Callable[..., Any])


def get_a2a_client() -> A2AClientWrapper:
    """Get an A2A client instance.

    Returns:
        An A2A client instance

    Raises:
        ImportError: If the a2a-sdk package is not installed
    """
    # Use the A2AClient class directly to ensure mocking works in tests
    return A2AClient()


def requires_a2a(func: F) -> F:
    """Check that A2A is available before calling a function.

    Args:
        func: The function to decorate

    Returns:
        The decorated function.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not A2A_AVAILABLE:
            raise ImportError("A2A SDK is not available. Install it with: pip install a2a-sdk")
        return func(*args, **kwargs)

    return cast(F, wrapper)
