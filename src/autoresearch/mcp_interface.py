"""MCP protocol integration using fastmcp."""

from __future__ import annotations

from typing import Dict, Any

import anyio
from fastmcp import FastMCP, Client

from .logging_utils import get_logger
from .orchestration.orchestrator import Orchestrator
from .config import ConfigLoader

logger = get_logger(__name__)

_config_loader: ConfigLoader = ConfigLoader()


def create_server(host: str = "127.0.0.1", port: int = 8080) -> FastMCP:
    """Create a FastMCP server exposing the research tool."""
    config = _config_loader.load_config()
    server: FastMCP = FastMCP("Autoresearch", host=host, port=port)

    @server.tool
    async def research(query: str) -> dict[str, Any]:
        try:
            result = Orchestrator().run_query(query, config)
            return {
                "answer": result.answer,
                "citations": [
                    c.model_dump(mode="json") if hasattr(c, "model_dump") else c.dict()
                    for c in result.citations
                ],
                "reasoning": result.reasoning,
                "metrics": result.metrics,
            }
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
) -> Dict[str, Any]:
    """Send a query to an MCP server and return the result."""
    target = transport or f"http://{host}:{port}"

    async def _call() -> Dict[str, Any]:
        async with Client(target) as client:
            return await client.call_tool("research", {"query": query})

    return anyio.run(_call)
