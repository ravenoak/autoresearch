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

import asyncio
import importlib
import threading
import types
from typing import Any, Callable, List, Optional, cast
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.background import BackgroundTasks
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import (
    JSONResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from limits.util import parse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import ConfigLoader, ConfigModel, get_config

# Lazily import SlowAPI and fall back to a minimal stub when unavailable
from ..error_utils import format_error_for_api, get_error_info
from ..models import BatchQueryRequest, QueryRequest, QueryResponse
from ..orchestration import ReasoningMode
from ..orchestration.orchestrator import Orchestrator
from ..storage import StorageManager
from ..tracing import get_tracer, setup_tracing
from .deps import require_permission
from .errors import handle_rate_limit
from .streaming import query_stream_endpoint
from .webhooks import notify_webhook

# Predeclare optional SlowAPI types for static analysis
Limiter: Any
RateLimitExceeded: type[Exception]
_rate_limit_exceeded_handler: Callable[..., Response]
Limit: Any
get_remote_address: Callable[[Request], str]

try:  # pragma: no cover - optional dependency
    _slowapi_module = importlib.import_module("slowapi")
    SLOWAPI_STUB = getattr(_slowapi_module, "IS_STUB", False)
    from slowapi import Limiter as SlowLimiter
    from slowapi import _rate_limit_exceeded_handler as SlowHandler
    from slowapi.errors import RateLimitExceeded as SlowRateLimitExceeded
    from slowapi.util import get_remote_address as SlowGetRemoteAddress

    if not SLOWAPI_STUB:
        from slowapi.wrappers import Limit as SlowLimit

    Limiter = SlowLimiter
    RateLimitExceeded = SlowRateLimitExceeded
    _rate_limit_exceeded_handler = SlowHandler
    get_remote_address = SlowGetRemoteAddress
    if not SLOWAPI_STUB:
        Limit = SlowLimit
    else:
        Limit = type("Limit", (), {})
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    SLOWAPI_STUB = True

    class _FallbackRateLimitExceeded(Exception):
        """Fallback exception raised when the rate limit is exceeded."""

    def _fallback_get_remote_address(request: Request) -> str:
        return request.client.host if request.client else "unknown"

    class _FallbackLimiter:  # pragma: no cover - simple stub
        def __init__(self, *_, **__):
            self.limiter = types.SimpleNamespace(hit=lambda *_a, **_k: True)

        def _inject_headers(self, response: Response, *_a, **_k):
            return response

    def _fallback_rate_limit_exceeded_handler(*_a: Any, **_k: Any) -> Response:
        return PlainTextResponse("rate limit exceeded", status_code=429)

    class _FallbackLimit:  # pragma: no cover - simple stub
        def __init__(self, *_, **__):
            pass

    RateLimitExceeded = _FallbackRateLimitExceeded
    get_remote_address = _fallback_get_remote_address
    Limiter = _FallbackLimiter
    _rate_limit_exceeded_handler = _fallback_rate_limit_exceeded_handler
    Limit = _FallbackLimit


class RequestLogger:
    """Thread-safe per-client request logger."""

    def __init__(self) -> None:
        self._log: dict[str, int] = {}
        self._lock = threading.Lock()

    def log(self, ip: str) -> int:
        """Record a request from ``ip`` and return the new count.

        This method is thread-safe.
        """
        with self._lock:
            self._log[ip] = self._log.get(ip, 0) + 1
            return self._log[ip]

    def reset(self) -> None:
        """Clear all recorded requests.

        This method is thread-safe.
        """
        with self._lock:
            self._log.clear()

    def get(self, ip: str) -> int:
        """Return the number of requests from ``ip``.

        Returns ``0`` if the IP has not been logged yet. This method is
        thread-safe.
        """
        with self._lock:
            return self._log.get(ip, 0)

    def snapshot(self) -> dict[str, int]:
        """Return a copy of the current log state."""
        with self._lock:
            return dict(self._log)


def create_request_logger() -> RequestLogger:
    """Factory for creating a new :class:`RequestLogger` instance."""
    return RequestLogger()


def get_request_logger(app: FastAPI | None = None) -> RequestLogger:
    """Retrieve the application's request logger."""
    if app is None:
        app = cast(FastAPI, globals().get("app"))
    return cast(RequestLogger, app.state.request_logger)


def reset_request_log(app: FastAPI | None = None) -> None:
    """Clear the application's request log."""
    get_request_logger(app).reset()


security = HTTPBearer(auto_error=False)
router = APIRouter()


class AuthMiddleware(BaseHTTPMiddleware):
    """API key and token authentication middleware."""

    def _resolve_role(self, key: str | None, cfg) -> tuple[str, JSONResponse | None]:
        if cfg.api_keys:
            role = cfg.api_keys.get(key)
            if not role:
                return "anonymous", JSONResponse(
                    {"detail": "Invalid API key"}, status_code=401
                )
            return role, None
        if cfg.api_key:
            if key != cfg.api_key:
                return "anonymous", JSONResponse(
                    {"detail": "Invalid API key"}, status_code=401
                )
            return "user", None
        return "anonymous", None

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/docs", "/openapi.json"}:
            return await call_next(request)
        loader = cast(ConfigLoader, request.app.state.config_loader)
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


class FallbackRateLimitMiddleware(BaseHTTPMiddleware):
    """Simplified rate limiting used when SlowAPI is unavailable."""

    def __init__(self, app, request_logger: RequestLogger, limiter: Limiter):
        super().__init__(app)
        self.request_logger = request_logger
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
        cfg_limit = getattr(get_config().api, "rate_limit", 0)
        if cfg_limit:
            ip = get_remote_address(request)
            count = self.request_logger.log(ip)
            limit_obj = parse(dynamic_limit())
            request.state.view_rate_limit = (limit_obj, [ip])
            if count > cfg_limit:
                if SLOWAPI_STUB:
                    return handle_rate_limit(
                        request, RateLimitExceeded(cast("Limit", None))
                    )
                limit_wrapper = Limit(
                    limit_obj,
                    get_remote_address,
                    None,
                    False,
                    None,
                    None,
                    None,
                    1,
                    False,
                )
                return handle_rate_limit(request, RateLimitExceeded(limit_wrapper))
        response = await call_next(request)
        if cfg_limit and not SLOWAPI_STUB:
            response = self.limiter._inject_headers(
                response, request.state.view_rate_limit
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting using SlowAPI's limiter with dynamic configuration."""

    def __init__(self, app, request_logger: RequestLogger, limiter: Limiter):
        super().__init__(app)
        self.request_logger = request_logger
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
        cfg_limit = getattr(get_config().api, "rate_limit", 0)
        if cfg_limit:
            ip = get_remote_address(request)
            count = self.request_logger.log(ip)
            limit_obj = parse(dynamic_limit())
            request.state.view_rate_limit = (limit_obj, [ip])
            if not self.limiter.limiter.hit(limit_obj, ip) or count > cfg_limit:
                limit_wrapper = Limit(
                    limit_obj,
                    get_remote_address,
                    None,
                    False,
                    None,
                    None,
                    None,
                    1,
                    False,
                )
                return handle_rate_limit(request, RateLimitExceeded(limit_wrapper))
            response = await call_next(request)
            return self.limiter._inject_headers(response, request.state.view_rate_limit)
        return await call_next(request)


router.post("/query/stream")(query_stream_endpoint)


@router.get("/docs", include_in_schema=False)
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


@router.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema(request: Request):
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
        routes=request.app.routes,
    )
    return openapi_schema


@router.post("/query", response_model=None)
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
                notify_webhook(request.webhook_url, error_resp, timeout)
            for url in getattr(config.api, "webhooks", []):
                notify_webhook(url, error_resp, timeout)
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
            notify_webhook(request.webhook_url, error_resp, timeout)
        for url in getattr(config.api, "webhooks", []):
            notify_webhook(url, error_resp, timeout)
        return error_resp
    timeout = getattr(config.api, "webhook_timeout", 5)
    if request.webhook_url:
        notify_webhook(request.webhook_url, validated, timeout)
    for url in getattr(config.api, "webhooks", []):
        notify_webhook(url, validated, timeout)
    return validated


@router.post(
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
    selected = batch.queries[start : start + page_size]  # noqa: E203

    async def run_one(
        idx: int, q: QueryRequest, results: list[Optional[QueryResponse]]
    ) -> None:
        from . import query_endpoint as api_query_endpoint

        results[idx] = cast(QueryResponse, await api_query_endpoint(q))

    results: list[Optional[QueryResponse]] = [None for _ in selected]
    async with asyncio.TaskGroup() as tg:
        for idx, query in enumerate(selected):
            tg.create_task(run_one(idx, query, results))

    return {
        "page": page,
        "page_size": page_size,
        "results": cast(List[QueryResponse], results),
    }


@router.post("/query/async")
async def async_query_endpoint(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
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
    loop = asyncio.get_running_loop()
    future: asyncio.Future[QueryResponse] = loop.create_future()
    http_request.app.state.async_tasks[query_id] = future

    async def run_and_notify() -> None:
        try:
            result = await Orchestrator.run_query_async(request.query, config)
            future.set_result(result)
        except Exception as exc:  # pragma: no cover - defensive
            future.set_exception(exc)
            return
        timeout = getattr(config.api, "webhook_timeout", 5)
        if request.webhook_url:
            notify_webhook(request.webhook_url, result, timeout)
        for url in getattr(config.api, "webhooks", []):
            notify_webhook(url, result, timeout)

    def start_task() -> None:
        threading.Thread(
            target=lambda: asyncio.run(run_and_notify()), daemon=True
        ).start()

    background_tasks.add_task(start_task)
    return {"query_id": query_id}


@router.get("/query/{query_id}")
async def query_status_endpoint(
    query_id: str,
    http_request: Request,
    _: None = require_permission("query"),
) -> QueryResponse | dict:
    """Return the status or result of an asynchronous query."""
    task: asyncio.Task | None = http_request.app.state.async_tasks.get(query_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Unknown query ID")
    if not task.done():
        return {"status": "running"}
    try:
        result = task.result()
    except Exception as exc:
        del http_request.app.state.async_tasks[query_id]
        raise HTTPException(status_code=500, detail=str(exc))
    del http_request.app.state.async_tasks[query_id]
    return result


@router.delete("/query/{query_id}")
async def cancel_query_endpoint(
    query_id: str,
    http_request: Request,
    _: None = require_permission("query"),
) -> dict:
    """Cancel a running asynchronous query and remove it."""
    task: asyncio.Task | None = http_request.app.state.async_tasks.pop(query_id, None)
    if task is None:
        raise HTTPException(status_code=404, detail="Unknown query ID")
    if not task.done():
        task.cancel()
        return {"status": "cancelled"}
    return {"status": "finished"}


@router.get("/metrics")
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


@router.get("/health")
def health_endpoint() -> dict:
    """Simple health check endpoint.

    Returns a JSON object indicating the server is running. This endpoint can be
    used by deployment tooling or load balancers to verify the service status.
    """

    return {"status": "ok"}


@router.get("/capabilities")
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


@router.get("/config")
def get_config_endpoint(_: None = require_permission("capabilities")) -> dict:
    """Return the current configuration."""
    return get_config().model_dump(mode="json")


@router.put("/config")
def update_config_endpoint(
    updates: dict,
    request: Request,
    _: None = require_permission("capabilities"),
) -> dict:
    """Update configuration at runtime."""
    loader = cast(ConfigLoader, request.app.state.config_loader)
    current = loader.config.model_dump(mode="python")
    current.update(updates)
    try:
        new_cfg = ConfigModel(**current)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    loader._config = new_cfg
    loader.notify_observers(new_cfg)
    return new_cfg.model_dump(mode="json")


@router.post("/config")
def replace_config_endpoint(
    new_config: dict,
    request: Request,
    _: None = require_permission("capabilities"),
) -> dict:
    """Replace the entire configuration at runtime."""
    loader = cast(ConfigLoader, request.app.state.config_loader)
    try:
        new_cfg = ConfigModel(**new_config)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    loader._config = new_cfg
    loader.notify_observers(new_cfg)
    return new_cfg.model_dump(mode="json")


@router.delete("/config")
def reload_config_endpoint(
    request: Request, _: None = require_permission("capabilities")
) -> dict:
    """Reload configuration from disk and discard runtime changes."""
    loader = cast(ConfigLoader, request.app.state.config_loader)
    try:
        new_cfg = loader.load_config()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))
    loader._config = new_cfg
    loader.notify_observers(new_cfg)
    return new_cfg.model_dump(mode="json")


def create_app(
    config_loader: ConfigLoader | None = None,
    request_logger: RequestLogger | None = None,
    limiter: Limiter | None = None,
) -> FastAPI:
    """Application factory for creating isolated FastAPI instances."""
    app = FastAPI(
        title="Autoresearch API",
        description="API for interacting with the Autoresearch system",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
    )
    app.add_middleware(AuthMiddleware)

    limiter = limiter or Limiter(key_func=get_remote_address)
    app.state.limiter = limiter

    request_logger = request_logger or create_request_logger()
    app.state.request_logger = request_logger

    if SLOWAPI_STUB:
        app.add_middleware(
            FallbackRateLimitMiddleware,
            request_logger=request_logger,
            limiter=limiter,
        )
    else:
        app.add_middleware(
            RateLimitMiddleware,
            request_logger=request_logger,
            limiter=limiter,
        )

    loader = config_loader or ConfigLoader()
    app.state.config_loader = loader
    app.state.async_tasks = {}

    @app.on_event("startup")
    def _startup() -> None:
        StorageManager.setup()
        watch_ctx = loader.watching()
        watch_ctx.__enter__()
        app.state.watch_ctx = watch_ctx

    @app.on_event("shutdown")
    def _stop_config_watcher() -> None:
        try:
            watch_ctx = getattr(app.state, "watch_ctx", None)
            if watch_ctx is not None:
                watch_ctx.__exit__(None, None, None)
                app.state.watch_ctx = None
        finally:
            loader.stop_watching()

    app.include_router(router)
    app.add_exception_handler(RateLimitExceeded, handle_rate_limit)
    return app


# Default application instance used by the package
app = create_app()
config_loader = cast(ConfigLoader, app.state.config_loader)
limiter = app.state.limiter
