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
from typing import Any, Callable, Dict
from uuid import uuid4

import httpx
import uvicorn
from pydantic import BaseModel

# Import ``pydantic.root_model`` early to avoid compatibility issues when the
# A2A SDK uses generics with Pydantic 2.
try:  # pragma: no cover - runtime import patch
    import sys

    import pydantic.root_model as _rm  # noqa: F401

    sys.modules.setdefault("pydantic.root_model", _rm)
except Exception:  # pragma: no cover - best effort
    pass

try:
    from a2a.client import A2AClient as SDKA2AClient
    from a2a.types import (
        Message,
        MessageSendParams,
        SendMessageRequest,
        SendMessageResponse,
    )
    from a2a.utils.message import get_message_text, new_agent_text_message

    A2A_AVAILABLE = True

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

        type: A2AMessageType
        message: Message

    class A2AServer:
        """FastAPI/uvicorn server for A2A messages."""

        def __init__(self, host: str, port: int) -> None:
            self.host = host
            self.port = port
            self._handlers: Dict[str, Callable[[Message], Dict[str, Any]]] = {}
            self._server: uvicorn.Server | None = None
            self._thread: Thread | None = None

        def register_handler(
            self,
            message_type: str | A2AMessageType,
            handler: Callable[[Message], Dict[str, Any]],
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

        async def _dispatch(self, msg_type: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch a request to the appropriate handler."""

            handler = self._handlers.get(msg_type)
            if handler is None:
                return {"status": "error", "error": "Unknown message type"}
            message = Message.model_validate(message_data)
            if asyncio.iscoroutinefunction(handler):
                return await handler(message)
            return await asyncio.to_thread(handler, message)

        def start(self) -> None:
            """Start the HTTP server in a background thread."""

            from fastapi import FastAPI

            app = FastAPI()

            @app.post("/")
            async def handle(
                payload: Dict[str, Any],
            ) -> Dict[str, Any]:  # pragma: no cover - network
                msg_type = str(payload.get("type", ""))
                message_data = payload.get("message", {})
                return await self._dispatch(msg_type, message_data)

            config = uvicorn.Config(app, host=self.host, port=self.port, log_level="info")
            self._server = uvicorn.Server(config)
            server = self._server

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

except ImportError:  # pragma: no cover - dependency missing
    A2A_AVAILABLE = False

from pydantic import ValidationError

from .api import capabilities_endpoint
from .config import ConfigLoader, ConfigModel, get_config
from .error_utils import format_error_for_a2a, get_error_info
from .logging_utils import get_logger
from .orchestration.orchestrator import Orchestrator

logger = get_logger(__name__)


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

    async def _handle_query(self, message: Message) -> Dict[str, Any]:
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
            # Process the query using the asynchronous orchestrator to allow
            # multiple requests to run concurrently without blocking the event
            # loop.
            result = await self.orchestrator.run_query_async(query, get_config())

            response_msg: Message = new_agent_text_message(result.answer)

            return {
                "status": "success",
                "message": response_msg.model_dump(mode="json"),
            }
        except Exception as e:
            # Get error information with suggestions and code examples
            error_info = get_error_info(e)
            error_data = format_error_for_a2a(error_info)

            # Log the error
            logger.error(f"Error processing query: {e}", exc_info=e)

            # Return error response
            return error_data

    def _handle_command(self, message: Message) -> Dict[str, Any]:
        """Handle a command message from another agent.

        Args:
            message: The incoming A2A message

        Returns:
            The response A2A message
        """
        command = ""
        args: Dict[str, Any] = {}
        if message.metadata:
            command = message.metadata.get("command", "")
            args = message.metadata.get("args", {})
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
            error_data = format_error_for_a2a(error_info)

            # Log the error
            logger.error(f"Error handling command {command}: {e}", exc_info=e)

            # Return error response
            return error_data

    def _handle_info(self, message: Any) -> Dict[str, Any]:
        """Handle an info message from another agent.

        Args:
            message: The incoming A2A message

        Returns:
            The response A2A message with agent information
        """
        try:
            # Get package version from the environment or use a default
            version = os.environ.get("AUTORESEARCH_VERSION", "0.1.0")

            agent_info = {
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

            return {
                "status": "success",
                "agent_info": agent_info,
                "message": info_msg.model_dump(mode="json"),
            }
        except Exception as e:
            # Get error information with suggestions and code examples
            error_info = get_error_info(e)
            error_data = format_error_for_a2a(error_info)

            # Log the error
            logger.error(f"Error handling info message: {e}", exc_info=e)

            # Return error response
            return error_data

    def _handle_get_capabilities(self) -> Any:
        """Handle a get_capabilities command.

        Returns:
            The capabilities information as a dictionary.
        """
        capabilities = capabilities_endpoint()
        return capabilities

    def _handle_get_config(self) -> Any:
        """Handle a get_config command.

        Returns:
            The current configuration as a dictionary.
        """
        config = get_config()
        return config.model_dump(mode="json")

    def _handle_set_config(self, args: Dict[str, Any]) -> Any:
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
            return format_error_for_a2a(error_info)

        loader._config = new_config
        loader.notify_observers(new_config)
        return new_config.model_dump(mode="json")


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

    def _send_request(self, agent_url: str, params: MessageSendParams) -> Dict[str, Any]:
        """Send a message request and return the raw response as a dict."""

        async def _run() -> SendMessageResponse:
            async with httpx.AsyncClient() as http_client:
                client = SDKA2AClient(http_client, url=agent_url)
                request = SendMessageRequest(id=str(uuid4()), params=params)
                return await client.send_message(request)

        response = asyncio.run(_run())
        return response.model_dump(mode="python")

    def query_agent(self, agent_url: str, query: str) -> Dict[str, Any]:
        """Send a query to another agent.

        Args:
            agent_url: The URL of the agent to query
            query: The query to send

        Returns:
            The response from the agent
        """
        try:
            params = MessageSendParams(message=new_agent_text_message(query))
            response = self._send_request(agent_url, params)

            if "error" in response:
                logger.error(f"Error querying agent: {response.get('error')}")
                return {"error": response.get("error")}

            result = response.get("result", {})
            if isinstance(result, dict) and result.get("kind") == "message" and result.get("parts"):
                part = result["parts"][0]
                if isinstance(part, dict) and "text" in part:
                    return {"answer": part["text"]}

            return result
        except Exception as e:
            logger.error(f"Error querying agent: {e}")
            return {"error": str(e)}

    def get_agent_capabilities(self, agent_url: str) -> Dict[str, Any]:
        """Get the capabilities of another agent.

        Args:
            agent_url: The URL of the agent

        Returns:
            The capabilities of the agent
        """
        try:
            params = MessageSendParams(message=new_agent_text_message("get_capabilities"))
            response = self._send_request(agent_url, params)

            if "error" in response:
                logger.error(f"Error getting agent capabilities: {response.get('error')}")
                return {"error": response.get("error")}

            return response.get("result", {})
        except Exception as e:
            logger.error(f"Error getting agent capabilities: {e}")
            return {"error": str(e)}

    def get_agent_config(self, agent_url: str) -> Dict[str, Any]:
        """Get the configuration of another agent.

        Args:
            agent_url: The URL of the agent

        Returns:
            The configuration of the agent
        """
        try:
            params = MessageSendParams(message=new_agent_text_message("get_config"))
            response = self._send_request(agent_url, params)

            if "error" in response:
                logger.error(f"Error getting agent config: {response.get('error')}")
                return {"error": response.get("error")}

            return response.get("result", {})
        except Exception as e:
            logger.error(f"Error getting agent config: {e}")
            return {"error": str(e)}

    def set_agent_config(self, agent_url: str, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update the configuration of another agent.

        Args:
            agent_url: The URL of the agent
            config_updates: The configuration updates to apply

        Returns:
            The result of the configuration update
        """
        try:
            params = MessageSendParams(
                message=new_agent_text_message("set_config"),
                metadata={"args": config_updates},
            )
            response = self._send_request(agent_url, params)

            if "error" in response:
                logger.error(f"Error setting agent config: {response.get('error')}")
                return {"error": response.get("error")}

            return response.get("result", {})
        except Exception as e:
            logger.error(f"Error setting agent config: {e}")
            return {"error": str(e)}


# Alias for backward compatibility
A2AClient = A2AClientWrapper  # noqa: F811


def get_a2a_client() -> A2AClientWrapper:
    """Get an A2A client instance.

    Returns:
        An A2A client instance

    Raises:
        ImportError: If the a2a-sdk package is not installed
    """
    # Use the A2AClient class directly to ensure mocking works in tests
    return A2AClient()


def requires_a2a(func: Callable) -> Callable:
    """Check that A2A is available before calling a function.

    Args:
        func: The function to decorate

    Returns:
        The decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not A2A_AVAILABLE:
            raise ImportError("A2A SDK is not available. Install it with: pip install a2a-sdk")
        return func(*args, **kwargs)

    return wrapper
