"""A2A (Agent-to-Agent) interface for Autoresearch.

This module provides integration with the A2A protocol, allowing Autoresearch
to be used as an agent in A2A-compatible systems. It implements the necessary
handlers and adapters to expose Autoresearch functionality through the A2A SDK.
"""

from __future__ import annotations

import os
import asyncio
from functools import wraps
from typing import Any, Callable, Dict
from uuid import uuid4

import httpx

try:
    from a2a.client import A2AClient as SDKA2AClient

    from a2a.utils.message import new_agent_text_message
    from a2a.types import (
        Message,
        MessageSendParams,
        SendMessageRequest,
        SendMessageResponse,
    )
    # The A2AServer, A2AMessage, and A2AMessageType classes are not directly available
    # in the a2a package. We'll need to adapt our code to use the available classes.
    A2A_AVAILABLE = True

    # Define stub classes for testing purposes
    class A2AServer:
        """Stub class for A2AServer."""

        def __init__(self, host=None, port=None):
            """Initialize the stub server with host and port."""
            self.host = host
            self.port = port

        def register_handler(self, message_type, handler):
            """Register a handler for a message type."""
            pass

        def start(self):
            """Start the server."""
            pass

        def stop(self):
            """Stop the server."""
            pass

    class A2AMessage:
        """Stub class for A2AMessage."""

        def __init__(self, type=None, content=None):
            """Initialize a stub message."""
            self.type = type
            self.content = content or {}

    class A2AMessageType:
        """Stub class for A2AMessageType."""

        QUERY = "query"
        COMMAND = "command"
        INFO = "info"
        RESULT = "result"
        ERROR = "error"
        ACK = "ack"
except ImportError:
    A2A_AVAILABLE = False

from .logging_utils import get_logger
from .orchestration.orchestrator import Orchestrator
from .error_utils import get_error_info, format_error_for_a2a
from .config import get_config, ConfigLoader, ConfigModel
from .api import capabilities_endpoint
from pydantic import ValidationError

logger = get_logger(__name__)


class A2AInterface:
    """Interface for integrating Autoresearch with A2A protocol."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        """Initialize the A2A interface.

        Args:
            host: The host to bind the A2A server to
            port: The port to bind the A2A server to

        Raises:
            ImportError: If the a2a-sdk package is not installed
        """
        if not A2A_AVAILABLE:
            raise ImportError(
                "The a2a-sdk package is required for A2A integration. "
                "Install it with: pip install a2a-sdk"
            )

        self.host = host
        self.port = port
        # Using the stub A2AServer class for testing purposes
        self.server = A2AServer(host=host, port=port)
        self.orchestrator = Orchestrator()

        # Register message handlers
        self.server.register_handler(A2AMessageType.QUERY, self._handle_query)
        self.server.register_handler(A2AMessageType.COMMAND, self._handle_command)
        self.server.register_handler(A2AMessageType.INFO, self._handle_info)
        logger.warning("Using stub A2AServer class. Server functionality is limited.")

    def start(self) -> None:
        """Start the A2A server."""
        logger.info(f"Starting A2A server on {self.host}:{self.port}")
        self.server.start()

    def stop(self) -> None:
        """Stop the A2A server."""
        logger.info("Stopping A2A server")
        self.server.stop()

    def _handle_query(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle a query message from another agent.

        Args:
            message: The incoming A2A message

        Returns:
            The response A2A message
        """
        query = message.content.get("query", "")
        if not query:
            return {"status": "error", "error": "No query provided"}

        try:
            # Process the query using the orchestrator
            result = self.orchestrator.run_query(query, get_config())

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

    def _handle_command(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle a command message from another agent.

        Args:
            message: The incoming A2A message

        Returns:
            The response A2A message
        """
        command = message.content.get("command", "")
        args = message.content.get("args", {})

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

            return {"status": "success", "agent_info": agent_info, "message": info_msg.model_dump(mode="json")}
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
            The response A2A message with capabilities information

        Raises:
            NotImplementedError: A2AMessage and A2AMessageType are not implemented
        """
        capabilities = capabilities_endpoint()
        return capabilities

    def _handle_get_config(self) -> Any:
        """Handle a get_config command.

        Returns:
            The response A2A message with configuration information

        Raises:
            NotImplementedError: A2AMessage and A2AMessageType are not implemented
        """
        config = get_config()
        return config.model_dump(mode="json")

    def _handle_set_config(self, args: Dict[str, Any]) -> Any:
        """Handle a set_config command.

        Args:
            args: The command arguments containing configuration updates

        Returns:
            The response A2A message

        Raises:
            NotImplementedError: A2AMessage and A2AMessageType are not implemented
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

        logger.warning(
            "A2AMessage and A2AMessageType are not implemented. Client functionality is limited."
        )

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
                logger.error(
                    f"Error querying agent: {response.get('error')}")
                return {"error": response.get("error")}

            result = response.get("result", {})
            if (
                isinstance(result, dict)
                and result.get("kind") == "message"
                and result.get("parts")
            ):
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
                logger.error(
                    f"Error getting agent capabilities: {response.get('error')}"
                )
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
                logger.error(
                    f"Error getting agent config: {response.get('error')}"
                )
                return {"error": response.get("error")}

            return response.get("result", {})
        except Exception as e:
            logger.error(f"Error getting agent config: {e}")
            return {"error": str(e)}

    def set_agent_config(
        self, agent_url: str, config_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
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
                logger.error(
                    f"Error setting agent config: {response.get('error')}"
                )
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
        NotImplementedError: A2AMessage and A2AMessageType are not implemented
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
            raise ImportError(
                "A2A SDK is not available. Install it with: pip install a2a-sdk"
            )
        return func(*args, **kwargs)

    return wrapper
