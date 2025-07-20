"""FastAPI API for Autoresearch.

This module provides a FastAPI-based HTTP API for interacting with the Autoresearch system.
It includes endpoints for submitting queries, retrieving metrics, and handles configuration
hot-reloading during the application's lifetime.

The API automatically initializes the storage system on startup and properly cleans up
resources on shutdown. It also provides error handling for various failure scenarios,
ensuring that clients always receive a valid response.

Endpoints:
    POST /query: Submit a query to the Autoresearch system
    GET /metrics: Retrieve Prometheus metrics for monitoring
    GET /openapi.json: OpenAPI schema documentation
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import PlainTextResponse, JSONResponse, StreamingResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, cast, TYPE_CHECKING
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
if TYPE_CHECKING:
    from slowapi.wrappers import Limit
from starlette.types import ExceptionHandler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
import importlib
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)
from .config import ConfigLoader, get_config, ConfigModel
import asyncio
from uuid import uuid4
import httpx
from .orchestration.orchestrator import Orchestrator
from .orchestration import ReasoningMode
from .tracing import get_tracer, setup_tracing
from .models import QueryRequest, QueryResponse, BatchQueryRequest
from .storage import StorageManager
from pydantic import ValidationError
from .error_utils import get_error_info, format_error_for_api

_slowapi_module = importlib.import_module("slowapi")
SLOWAPI_STUB = getattr(_slowapi_module, "IS_STUB", False)
# Global per-client request log used for fallback rate limiting and tests
REQUEST_LOG: dict[str, int] = {}


def reset_request_log() -> None:
    """Clear the request log."""
    REQUEST_LOG.clear()


config_loader = ConfigLoader()

security = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """API key and token authentication middleware."""

    def _resolve_role(self, key: str | None, cfg) -> tuple[str, JSONResponse | None]:
        if cfg.api_keys:
            role = cfg.api_keys.get(key)
            if not role:
                return "anonymous", JSONResponse({"detail": "Invalid API key"}, status_code=401)
            return role, None
        if cfg.api_key:
            if key != cfg.api_key:
                return "anonymous", JSONResponse({"detail": "Invalid API key"}, status_code=401)
            return "user", None
        return "anonymous", None

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/docs", "/openapi.json"}:
            return await call_next(request)
        loader = ConfigLoader()
        loader._config = loader.load_config()
        cfg = loader._config.api
        role, error = self._resolve_role(request.headers.get("X-API-Key"), cfg)
        if error:
            return error
        request.state.role = role
        request.state.permissions = set(cfg.role_permissions.get(role, []))
        if cfg.bearer_token:
            credentials: HTTPAuthorizationCredentials | None = await security(request)
            token = credentials.credentials if credentials else None
            if token != cfg.bearer_token:
                return JSONResponse({"detail": "Invalid token"}, status_code=401)
        return await call_next(request)


def dynamic_limit() -> str:
    limit = getattr(get_config().api, "rate_limit", 0)
    return f"{limit}/minute" if limit > 0 else "1000000/minute"


def require_permission(permission: str):
    async def checker(request: Request) -> None:
        permissions: set[str] = getattr(request.state, "permissions", set())
        if permission not in permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    return Depends(checker)


limiter = Limiter(key_func=get_remote_address, application_limits=[dynamic_limit])

app = FastAPI(
    title="Autoresearch API",
    description="API for interacting with the Autoresearch system",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)
app.add_middleware(AuthMiddleware)
app.state.limiter = limiter


class FallbackRateLimitMiddleware(BaseHTTPMiddleware):
    """Simplified rate limiting when SlowAPI is unavailable."""

    async def dispatch(self, request: Request, call_next):
        cfg_limit = getattr(get_config().api, "rate_limit", 0)
        if cfg_limit:
            ip = get_remote_address(request)
            REQUEST_LOG[ip] = REQUEST_LOG.get(ip, 0) + 1
            if SLOWAPI_STUB and REQUEST_LOG[ip] > cfg_limit:
                raise RateLimitExceeded(cast("Limit", None))
        return await call_next(request)


app.add_middleware(FallbackRateLimitMiddleware)


def _handle_rate_limit(request: Request, exc: RateLimitExceeded) -> Response:
    return _rate_limit_exceeded_handler(request, exc)


app.add_exception_handler(
    RateLimitExceeded, cast(ExceptionHandler, _handle_rate_limit)
)
app.add_middleware(SlowAPIMiddleware)
_watch_ctx = None
app.state.async_tasks = {}


def _notify_webhook(url: str, result: QueryResponse, timeout: float = 5) -> None:
    """Send the final result to a webhook URL if configured."""
    try:
        httpx.post(url, json=result.model_dump(), timeout=timeout)
    except Exception:
        pass  # pragma: no cover - ignore webhook errors


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Serve custom Swagger UI documentation.

    This endpoint serves a custom Swagger UI page with additional information
    about the API and how to use it. It provides an interactive interface for
    exploring and testing the API endpoints.

    Returns:
        HTMLResponse: The Swagger UI HTML page
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Autoresearch API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    """Serve the OpenAPI schema for the API.

    This endpoint returns the OpenAPI schema for the API, which describes all
    available endpoints, request/response models, and authentication requirements.
    This schema can be used by API clients to understand how to interact with the API.

    Returns:
        dict: The OpenAPI schema as a JSON object
    """
    openapi_schema = get_openapi(
        title="Autoresearch API",
        version="1.0.0",
        description="""
        # Autoresearch API

        This API allows you to interact with the Autoresearch system, a local-first research assistant
        that coordinates multiple agents to produce evidence-backed answers.

        ## Authentication

        Set `AUTORESEARCH_API_KEY` to require clients to pass the key in the `X-API-Key` header.
        If the variable is unset authentication is disabled.

        ## Rate Limiting

        Set `AUTORESEARCH_RATE_LIMIT` to the number of requests allowed per minute per client IP.
        When unset or `0`, throttling is disabled.

        ## Endpoints

        - **POST /query**: Submit a query to the Autoresearch system
        - **POST /query/stream**: Stream updates for a query
        - **POST /query/batch**: Execute multiple queries
        - **POST /query/async**: Run a query in the background
        - **GET /query/{id}**: Check the status of an async query
        - **DELETE /query/{id}**: Cancel a running async query
        - **GET /config**: Retrieve current configuration
        - **PUT /config**: Update configuration at runtime
        - **GET /metrics**: Retrieve Prometheus metrics for monitoring
        - **GET /capabilities**: Discover system capabilities
        """,
        routes=app.routes,
    )
    return openapi_schema


@app.on_event("startup")
def _startup() -> None:
    """Initialize storage and configuration watching on API startup.

    This function is automatically called when the FastAPI application starts.
    It performs two critical initialization tasks:
    1. Sets up the StorageManager to ensure storage backends are ready
    2. Starts watching the configuration files for changes, enabling hot-reloading

    The configuration watcher is stored in a global variable to ensure it can be
    properly cleaned up during application shutdown.

    Returns:
        None
    """
    StorageManager.setup()
    global _watch_ctx
    _watch_ctx = config_loader.watching()
    _watch_ctx.__enter__()


# Start watching the main configuration file during the application's lifetime.


@app.on_event("shutdown")
def _stop_config_watcher() -> None:
    """Stop the configuration watcher thread when the app shuts down.

    This function is automatically called when the FastAPI application shuts down.
    It ensures that the configuration watcher context manager is properly exited,
    which stops the background thread that watches for configuration changes.

    Proper cleanup is important to prevent resource leaks and ensure the application
    can be restarted cleanly. This function checks if the watcher context exists
    before attempting to exit it, making it safe to call even if startup failed.

    Returns:
        None
    """
    global _watch_ctx
    if _watch_ctx is not None:
        _watch_ctx.__exit__(None, None, None)
        _watch_ctx = None


@app.post("/query", response_model=None)
async def query_endpoint(
    request: QueryRequest,
    stream: bool = False,
    _: None = require_permission("query"),
) -> StreamingResponse | QueryResponse:
    """Process a query and return a structured response.

    This endpoint accepts a JSON payload containing a query string and optional
    configuration parameters. It processes the query using the Orchestrator,
    which coordinates multiple agents to produce an evidence-backed answer.

    The endpoint also supports dynamic configuration by allowing clients to override
    configuration values in the payload. Any key in the payload that matches a
    configuration attribute will be used to update the configuration for this query.
    Pass ``stream=true`` as a query parameter to receive newline-delimited JSON
    updates instead of a single response.

    Args:
        request (QueryRequest): A request object containing:
            - query (str): The query string to process (required)
            - reasoning_mode (ReasoningMode, optional): The reasoning mode to use
            - loops (int, optional): The number of reasoning loops to perform
            - llm_backend (str, optional): The LLM backend to use

    Returns:
        QueryResponse: A structured response containing:
            - answer (str): The synthesized answer to the query
            - citations (list): Evidence supporting the answer
            - reasoning (list): Explanation of the reasoning process
            - metrics (dict): Performance metrics for the query

    Raises:
        HTTPException: If the query field is missing or empty
    """
    config = get_config()

    if stream:
        return await query_stream_endpoint(request)

    # Update config with parameters from the request
    if request.reasoning_mode is not None:
        config.reasoning_mode = ReasoningMode(request.reasoning_mode.value)
    if request.loops is not None:
        config.loops = request.loops
    if request.llm_backend is not None:
        config.llm_backend = request.llm_backend

    setup_tracing(getattr(config, "tracing_enabled", False))
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("/query"):
        try:
            result = Orchestrator.run_query(request.query, config)
        except Exception as exc:
            # Get error information with suggestions and code examples
            error_info = get_error_info(exc)
            error_data = format_error_for_api(error_info)

            # Create reasoning with suggestions
            reasoning = ["An error occurred during processing."]
            if error_info.suggestions:
                for suggestion in error_info.suggestions:
                    reasoning.append(f"Suggestion: {suggestion}")
            else:
                reasoning.append("Please check the logs for details.")

            # Create a valid QueryResponse object with error information
            error_resp = QueryResponse(
                answer=f"Error: {error_info.message}",
                citations=[],
                reasoning=reasoning,
                metrics={"error": error_info.message, "error_details": error_data},
            )
            timeout = getattr(config.api, "webhook_timeout", 5)
            if request.webhook_url:
                _notify_webhook(request.webhook_url, error_resp, timeout)
            for url in getattr(config.api, "webhooks", []):
                _notify_webhook(url, error_resp, timeout)
            return error_resp
    try:
        validated = (
            result
            if isinstance(result, QueryResponse)
            else QueryResponse.model_validate(result)
        )
    except ValidationError as exc:  # pragma: no cover - should not happen
        # Get error information with suggestions and code examples
        error_info = get_error_info(exc)
        error_data = format_error_for_api(error_info)

        # Create reasoning with suggestions
        reasoning = ["The response format was invalid."]
        if error_info.suggestions:
            for suggestion in error_info.suggestions:
                reasoning.append(f"Suggestion: {suggestion}")
        else:
            reasoning.append("Please check the logs for details.")

        # Create a valid QueryResponse object with error information
        error_resp = QueryResponse(
            answer="Error: Invalid response format",
            citations=[],
            reasoning=reasoning,
            metrics={
                "error": "Invalid response format",
                "validation_error": str(exc),
                "error_details": error_data,
            },
        )
        timeout = getattr(config.api, "webhook_timeout", 5)
        if request.webhook_url:
            _notify_webhook(request.webhook_url, error_resp, timeout)
        for url in getattr(config.api, "webhooks", []):
            _notify_webhook(url, error_resp, timeout)
        return error_resp
    timeout = getattr(config.api, "webhook_timeout", 5)
    if request.webhook_url:
        _notify_webhook(request.webhook_url, validated, timeout)
    for url in getattr(config.api, "webhooks", []):
        _notify_webhook(url, validated, timeout)
    return validated


@app.post("/query/stream")
async def query_stream_endpoint(
    request: QueryRequest,
    _: None = require_permission("query"),
) -> StreamingResponse:
    """Stream incremental query results as JSON lines."""
    config = get_config()

    if request.reasoning_mode is not None:
        config.reasoning_mode = ReasoningMode(request.reasoning_mode.value)
    if request.loops is not None:
        config.loops = request.loops
    if request.llm_backend is not None:
        config.llm_backend = request.llm_backend

    queue: asyncio.Queue[str | None] = asyncio.Queue()

    def on_cycle_end(loop_idx: int, state) -> None:
        queue.put_nowait(state.synthesize().model_dump_json())

    def run() -> None:
        try:
            result = Orchestrator.run_query(
                request.query, config, callbacks={"on_cycle_end": on_cycle_end}
            )
        except Exception as exc:  # pragma: no cover - defensive
            error_info = get_error_info(exc)
            error_data = format_error_for_api(error_info)
            reasoning = ["An error occurred during processing."]
            if error_info.suggestions:
                for suggestion in error_info.suggestions:
                    reasoning.append(f"Suggestion: {suggestion}")
            else:
                reasoning.append("Please check the logs for details.")
            result = QueryResponse(
                answer=f"Error: {error_info.message}",
                citations=[],
                reasoning=reasoning,
                metrics={"error": error_info.message, "error_details": error_data},
            )
        queue.put_nowait(result.model_dump_json())
        timeout = getattr(config.api, "webhook_timeout", 5)
        if request.webhook_url:
            _notify_webhook(request.webhook_url, result, timeout)
        for url in getattr(config.api, "webhooks", []):
            _notify_webhook(url, result, timeout)
        queue.put_nowait(None)

    asyncio.get_running_loop().run_in_executor(None, run)

    async def generator():
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item + "\n"

    return StreamingResponse(generator(), media_type="application/json")


@app.post(
    "/query/batch",
    summary="Batch Query Endpoint",
    description="Execute multiple queries with pagination support",
)
async def batch_query_endpoint(
    batch: BatchQueryRequest,
    page: int = 1,
    page_size: int = 10,
    _: None = require_permission("query"),
) -> dict:
    """Execute multiple queries with pagination."""
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")

    start = (page - 1) * page_size
    selected = batch.queries[start:start + page_size]

    async def run_one(idx: int, q: QueryRequest, results: list[Optional[QueryResponse]]) -> None:
        results[idx] = cast(QueryResponse, await query_endpoint(q))

    results: list[Optional[QueryResponse]] = [None for _ in selected]
    async with asyncio.TaskGroup() as tg:
        for idx, query in enumerate(selected):
            tg.create_task(run_one(idx, query, results))

    return {"page": page, "page_size": page_size, "results": cast(List[QueryResponse], results)}


@app.post("/query/async")
async def async_query_endpoint(
    request: QueryRequest,
    _: None = require_permission("query"),
) -> dict:
    """Run a query in the background and return its ID."""
    config = get_config()
    if request.reasoning_mode is not None:
        config.reasoning_mode = ReasoningMode(request.reasoning_mode.value)
    if request.loops is not None:
        config.loops = request.loops
    if request.llm_backend is not None:
        config.llm_backend = request.llm_backend

    query_id = str(uuid4())

    async def run() -> QueryResponse:
        return await Orchestrator.run_query_async(request.query, config)

    task = asyncio.create_task(run())
    app.state.async_tasks[query_id] = task

    def notify(_task: asyncio.Task) -> None:
        if _task.cancelled() or _task.exception():
            return
        result: QueryResponse = _task.result()
        timeout = getattr(config.api, "webhook_timeout", 5)
        if request.webhook_url:
            _notify_webhook(request.webhook_url, result, timeout)
        for url in getattr(config.api, "webhooks", []):
            _notify_webhook(url, result, timeout)

    task.add_done_callback(notify)
    return {"query_id": query_id}


@app.get("/query/{query_id}")
async def query_status_endpoint(
    query_id: str,
    _: None = require_permission("query"),
) -> QueryResponse | dict:
    """Return the status or result of an asynchronous query."""
    task: asyncio.Task | None = app.state.async_tasks.get(query_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Unknown query ID")
    if not task.done():
        return {"status": "running"}
    try:
        result = task.result()
    except Exception as exc:
        del app.state.async_tasks[query_id]
        raise HTTPException(status_code=500, detail=str(exc))
    del app.state.async_tasks[query_id]
    return result


@app.delete("/query/{query_id}")
async def cancel_query_endpoint(
    query_id: str,
    _: None = require_permission("query"),
) -> dict:
    """Cancel a running asynchronous query and remove it."""
    task: asyncio.Task | None = app.state.async_tasks.pop(query_id, None)
    if task is None:
        raise HTTPException(status_code=404, detail="Unknown query ID")
    if not task.done():
        task.cancel()
        return {"status": "cancelled"}
    return {"status": "finished"}


@app.get("/metrics")
def metrics_endpoint(_: None = require_permission("metrics")) -> PlainTextResponse:
    """Expose Prometheus metrics for monitoring the application.

    This endpoint generates and returns the latest Prometheus metrics in the
    standard text-based format. These metrics can be scraped by a Prometheus
    server to monitor various aspects of the application's performance and
    behavior, including:

    - Query processing times
    - Token usage
    - Error rates
    - Agent execution metrics
    - Storage system metrics

    Returns:
        PlainTextResponse: A response containing the latest Prometheus metrics
            in the standard text-based format with the appropriate content type.
    """
    data = generate_latest()
    return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health_endpoint() -> dict:
    """Simple health check endpoint.

    Returns a JSON object indicating the server is running. This endpoint can be
    used by deployment tooling or load balancers to verify the service status.
    """

    return {"status": "ok"}


@app.get("/capabilities")
def capabilities_endpoint(_: None = require_permission("capabilities")) -> dict:
    """Discover the capabilities of the Autoresearch system.

    This endpoint returns information about the capabilities of the Autoresearch system,
    including available reasoning modes, LLM backends, and other features. This information
    can be used by clients to understand what functionality is available and how to use it.

    Returns:
        dict: A dictionary containing capability information
    """
    config = get_config()

    # Get available reasoning modes
    from .models import ReasoningMode

    reasoning_modes = [mode.value for mode in ReasoningMode]

    # Get available LLM backends
    from .llm import get_available_adapters

    llm_backends = list(get_available_adapters().keys())

    # Get storage information
    storage_info = {
        "duckdb_path": config.storage.duckdb_path,
        "vector_extension": config.storage.vector_extension,
    }

    # Get search capabilities
    search_capabilities = {
        "max_results_per_query": config.search.max_results_per_query,
        "use_semantic_similarity": config.search.use_semantic_similarity,
    }

    # Get agent information
    agent_info = {
        "synthesizer": {
            "description": "Generates answers based on evidence",
            "role": "thesis",
        },
        "contrarian": {
            "description": "Challenges answers and identifies weaknesses",
            "role": "antithesis",
        },
        "factchecker": {
            "description": "Verifies factual accuracy of claims",
            "role": "synthesis",
        },
    }

    return {
        "version": "1.0.0",
        "reasoning_modes": reasoning_modes,
        "llm_backends": llm_backends,
        "storage": storage_info,
        "search": search_capabilities,
        "agents": agent_info,
        "current_config": {
            "reasoning_mode": config.reasoning_mode.value,
            "loops": config.loops,
            "llm_backend": config.llm_backend,
        },
    }


@app.get("/config")
def get_config_endpoint(_: None = require_permission("capabilities")) -> dict:
    """Return the current configuration."""
    return get_config().model_dump(mode="json")


@app.put("/config")
def update_config_endpoint(
    updates: dict,
    _: None = require_permission("capabilities"),
) -> dict:
    """Update configuration at runtime."""
    loader = ConfigLoader()
    current = loader.config.model_dump(mode="python")
    current.update(updates)
    try:
        new_cfg = ConfigModel(**current)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    loader._config = new_cfg
    loader.notify_observers(new_cfg)
    return new_cfg.model_dump(mode="json")


@app.post("/config")
def replace_config_endpoint(
    new_config: dict,
    _: None = require_permission("capabilities"),
) -> dict:
    """Replace the entire configuration at runtime."""
    loader = ConfigLoader()
    try:
        new_cfg = ConfigModel(**new_config)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    loader._config = new_cfg
    loader.notify_observers(new_cfg)
    return new_cfg.model_dump(mode="json")


@app.delete("/config")
def reload_config_endpoint(_: None = require_permission("capabilities")) -> dict:
    """Reload configuration from disk and discard runtime changes."""
    loader = ConfigLoader()
    try:
        new_cfg = loader.load_config()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))
    loader._config = new_cfg
    loader.notify_observers(new_cfg)
    return new_cfg.model_dump(mode="json")
