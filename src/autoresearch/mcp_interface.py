"""MCP protocol integration using fastmcp."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

import anyio
from fastmcp import Client, FastMCP

from .api.models import QueryRequestV1, QueryResponseV1
from .config import ConfigLoader
from .error_utils import format_error_for_api, get_error_info
from .logging_utils import get_logger
from .models import QueryResponse
from .orchestration.orchestrator import Orchestrator

logger = get_logger(__name__)

_config_loader: ConfigLoader = ConfigLoader()


def create_server(host: str = "127.0.0.1", port: int = 8080) -> FastMCP:
    """Create a FastMCP server exposing the research tool."""
    config = _config_loader.load_config()
    orchestrator = Orchestrator()
    server = _initialise_server(host=host, port=port)
    setattr(server, "orchestrator", orchestrator)

    @server.tool
    async def research(
        query: str | Mapping[str, Any],
        version: str = QueryRequestV1.__version__,
        **overrides: Any,
    ) -> dict[str, Any]:
        try:
            request = _build_query_request(query, version=version, overrides=overrides)
            result = orchestrator.run_query(request.query, config)
            return _build_success_payload(result)
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("Error processing query", exc_info=exc)
            return _build_error_payload(exc)

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
    payload = _build_request_payload(query)

    async def _call() -> dict[str, Any]:
        async with Client(target) as client:
            result = await client.call_tool("research", payload)
            response = QueryResponseV1.model_validate(result)
            result_payload: dict[str, Any] = response.model_dump(mode="json")
            return result_payload

    return anyio.run(_call)


def _initialise_server(host: str, port: int) -> FastMCP:
    """Construct a FastMCP server compatible with stubbed environments."""

    constructor_attempts: tuple[tuple[tuple[Any, ...], dict[str, Any]], ...] = (
        (("Autoresearch",), {"host": host, "port": port}),
        (("Autoresearch",), {}),
        (tuple(), {}),
    )
    for args, kwargs in constructor_attempts:
        try:
            server = FastMCP(*args, **kwargs)
            break
        except TypeError:
            continue
    else:  # pragma: no cover - defensive fallback
        server = FastMCP("Autoresearch")

    setattr(server, "host", host)
    setattr(server, "port", port)
    return server


def _build_request_payload(query: str) -> dict[str, Any]:
    """Render a versioned MCP payload for the research tool."""

    request = QueryRequestV1.model_validate({"query": query})
    return request.model_dump(mode="json")


def _build_query_request(
    query: str | Mapping[str, Any],
    *,
    version: str,
    overrides: Mapping[str, Any],
) -> QueryRequestV1:
    """Normalise inputs from FastMCP clients into ``QueryRequestV1``."""

    payload: dict[str, Any]
    if isinstance(query, Mapping):
        payload = {**_serialise_structure(query)}
    else:
        payload = {"query": query}
    payload.update(_serialise_structure(overrides))
    payload.setdefault("version", version)
    return QueryRequestV1.model_validate(payload)


def _build_success_payload(result: QueryResponse | Mapping[str, Any]) -> dict[str, Any]:
    """Serialise orchestrator responses using the public API schema."""

    if not isinstance(result, QueryResponse):
        result = QueryResponse.model_validate(result)
    payload = result.model_dump(mode="json")
    payload.update(
        {
            "citations": [
                _serialise_structure(item) for item in result.citations
            ],
            "claim_audits": [
                _serialise_structure(audit) for audit in result.claim_audits
            ],
            "react_traces": [
                _serialise_structure(trace) for trace in result.react_traces
            ],
            "metrics": _serialise_structure(result.metrics),
        }
    )
    response = QueryResponseV1.model_validate(payload)
    return response.model_dump(mode="json")


def _build_error_payload(exc: Exception) -> dict[str, Any]:
    """Return a structured error response mirroring the API contract."""

    error_info = get_error_info(exc)
    error_data = format_error_for_api(error_info)
    reasoning: list[str] = [
        "An error occurred during MCP query execution.",
    ]
    if error_info.suggestions:
        reasoning.extend(
            f"Socratic check: {suggestion}" for suggestion in error_info.suggestions
        )
    else:
        reasoning.append("Socratic check: Which configuration caused this failure?")

    response = QueryResponseV1(
        answer=f"Error: {error_info.message}",
        citations=[],
        reasoning=reasoning,
        metrics={
            "error": error_info.message,
            "error_details": _serialise_structure(error_data),
        },
    )
    return response.model_dump(mode="json")


def _serialise_structure(value: Any, *, _seen: set[int] | None = None) -> Any:
    """Convert nested structures into JSON-compatible primitives."""

    if _seen is None:
        _seen = set()

    if hasattr(value, "model_dump") and callable(value.model_dump):
        dumped = value.model_dump(mode="python")
        return _serialise_structure(dumped, _seen=_seen)
    if isinstance(value, Enum):
        return value.value
    obj_id = id(value)
    if obj_id in _seen:
        return repr(value)
    if isinstance(value, Mapping):
        _seen.add(obj_id)
        return {
            str(key): _serialise_structure(val, _seen=_seen) for key, val in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        _seen.add(obj_id)
        return [_serialise_structure(item, _seen=_seen) for item in value]
    attrs = getattr(value, "__dict__", None)
    if isinstance(attrs, Mapping):
        _seen.add(obj_id)
        return {
            str(key): _serialise_structure(val, _seen=_seen) for key, val in attrs.items()
        }
    if callable(value):
        return repr(value)
    return value
