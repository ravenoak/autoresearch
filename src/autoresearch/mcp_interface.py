"""MCP protocol integration using fastmcp."""

from __future__ import annotations

from typing import Any, Mapping, cast

import anyio
from fastmcp import FastMCP, Client

from .config import ConfigLoader
from .logging_utils import get_logger
from .models import QueryResponse
from .orchestration.orchestrator import Orchestrator

logger = get_logger(__name__)

_config_loader: ConfigLoader = ConfigLoader()


def create_server(host: str = "127.0.0.1", port: int = 8080) -> FastMCP:
    """Create a FastMCP server exposing the research tool."""
    config = _config_loader.load_config()
    orchestrator = Orchestrator()
    server: FastMCP = FastMCP("Autoresearch", host=host, port=port)
    setattr(server, "orchestrator", orchestrator)

    @server.tool
    async def research(query: str) -> dict[str, Any]:
        try:
            result: QueryResponse = orchestrator.run_query(query, config)
            response: dict[str, Any] = {
                "answer": result.answer,
                "citations": [_serialise_mapping(c) for c in result.citations],
                "reasoning": result.reasoning,
                "metrics": result.metrics,
            }
            return response
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("Error processing query", exc_info=exc)
            return {"error": str(exc)}

    return server


def query(
    query: str,
    host: str = "127.0.0.1",
    port: int = 8080,
    *,
    transport: FastMCP | None = None,
) -> dict[str, Any]:
    """Send a query to an MCP server and return the result."""
    target = transport or f"http://{host}:{port}"

    async def _call() -> dict[str, Any]:
        async with Client(target) as client:
            result = await client.call_tool("research", {"query": query})
            return cast(dict[str, Any], result)

    return anyio.run(_call)


def _serialise_mapping(value: Any) -> dict[str, Any] | Any:
    """Return a JSON-serialisable representation of ``value``."""

    if hasattr(value, "model_dump") and callable(value.model_dump):
        dumped = value.model_dump(mode="python")
        return cast(dict[str, Any], dumped)
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    attrs = getattr(value, "__dict__", None)
    if isinstance(attrs, Mapping):
        return {str(key): val for key, val in attrs.items()}
    return value
