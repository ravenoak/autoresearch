from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, List, Optional, cast
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import (
    JSONResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)
from pydantic import ValidationError

from ..config import ConfigLoader, ConfigModel, get_config
from ..error_utils import format_error_for_api, get_error_info
from ..models import BatchQueryRequest, QueryRequest, QueryResponse
from ..orchestration import ReasoningMode
from ..storage import StorageManager
from ..tracing import get_tracer, setup_tracing
from .deps import create_orchestrator, require_permission
from .errors import handle_rate_limit
from .middleware import (
    SLOWAPI_STUB,
    AuthMiddleware,
    FallbackRateLimitMiddleware,
    Limiter,
    RateLimitExceeded,
    RateLimitMiddleware,
    get_remote_address,
)
from .streaming import query_stream_endpoint
from .utils import (
    RequestLogger,
    create_request_logger,
)
from . import webhooks

router = APIRouter()

router.post("/query/stream", dependencies=[require_permission("query")])(query_stream_endpoint)


@router.get("/docs", include_in_schema=False, dependencies=[require_permission("docs")])
async def custom_swagger_ui_html() -> Response:
    """Serve custom Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Autoresearch API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@router.get("/openapi.json", include_in_schema=False, dependencies=[require_permission("docs")])
async def get_openapi_schema(request: Request) -> dict:
    """Serve the OpenAPI schema for the API."""
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
        - **GET /query/{query_id}**: Check the status of an async query
        - **DELETE /query/{query_id}**: Cancel a running async query
        - **GET /config**: Retrieve current configuration
        - **PUT /config**: Update configuration at runtime
        - **GET /health**: Check service status
        - **GET /metrics**: Retrieve Prometheus metrics for monitoring
        - **GET /capabilities**: Discover system capabilities
        """,
        routes=request.app.routes,
    )
    return openapi_schema


@router.post("/query", response_model=None, dependencies=[require_permission("query")])
async def query_endpoint(
    request: QueryRequest, stream: bool = False
) -> StreamingResponse | QueryResponse:
    """Process a query and return a structured response."""
    config = get_config()

    if stream:
        return await query_stream_endpoint(request)

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
            result = create_orchestrator().run_query(request.query, config)
        except Exception as exc:
            error_info = get_error_info(exc)
            error_data = format_error_for_api(error_info)
            reasoning = ["An error occurred during processing."]
            if error_info.suggestions:
                for suggestion in error_info.suggestions:
                    reasoning.append(f"Suggestion: {suggestion}")
            else:
                reasoning.append("Please check the logs for details.")
            error_resp = QueryResponse(
                answer=f"Error: {error_info.message}",
                citations=[],
                reasoning=reasoning,
                metrics={"error": error_info.message, "error_details": error_data},
            )
            timeout = getattr(config.api, "webhook_timeout", 5)
            if request.webhook_url:
                webhooks.notify_webhook(request.webhook_url, error_resp, timeout)
            for url in getattr(config.api, "webhooks", []):
                webhooks.notify_webhook(url, error_resp, timeout)
            return error_resp
    try:
        validated = (
            result if isinstance(result, QueryResponse) else QueryResponse.model_validate(result)
        )
    except ValidationError as exc:  # pragma: no cover - should not happen
        error_info = get_error_info(exc)
        error_data = format_error_for_api(error_info)
        reasoning = ["The response format was invalid."]
        if error_info.suggestions:
            for suggestion in error_info.suggestions:
                reasoning.append(f"Suggestion: {suggestion}")
        else:
            reasoning.append("Please check the logs for details.")
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
            webhooks.notify_webhook(request.webhook_url, error_resp, timeout)
        for url in getattr(config.api, "webhooks", []):
            webhooks.notify_webhook(url, error_resp, timeout)
        return error_resp
    timeout = getattr(config.api, "webhook_timeout", 5)
    if request.webhook_url:
        webhooks.notify_webhook(request.webhook_url, validated, timeout)
    for url in getattr(config.api, "webhooks", []):
        webhooks.notify_webhook(url, validated, timeout)
    return validated


@router.post(
    "/query/batch",
    summary="Batch Query Endpoint",
    description="Execute multiple queries with pagination support",
    dependencies=[require_permission("query")],
)
async def batch_query_endpoint(
    batch: BatchQueryRequest, page: int = 1, page_size: int = 10
) -> dict:
    """Execute multiple queries with pagination."""
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")

    start = (page - 1) * page_size
    selected = batch.queries[start : start + page_size]  # noqa: E203

    async def run_one(idx: int, q: QueryRequest, results: list[Optional[QueryResponse]]) -> None:
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


@router.post("/query/async", dependencies=[require_permission("query")])
async def async_query_endpoint(request: QueryRequest, http_request: Request) -> dict:
    """Run a query asynchronously and return its ID."""
    config = get_config()
    if request.reasoning_mode is not None:
        config.reasoning_mode = ReasoningMode(request.reasoning_mode.value)
    if request.loops is not None:
        config.loops = request.loops
    if request.llm_backend is not None:
        config.llm_backend = request.llm_backend

    task_id = str(uuid4())
    config_copy: ConfigModel = config.model_copy(deep=True)

    async def runner() -> QueryResponse | Any:
        try:
            orchestrator = cast(Any, create_orchestrator())
            return await orchestrator.run_query_async(request.query, config_copy)
        except Exception as exc:  # pragma: no cover - defensive
            error_info = get_error_info(exc)
            error_data = format_error_for_api(error_info)
            reasoning = ["An error occurred during processing."]
            if error_info.suggestions:
                for suggestion in error_info.suggestions:
                    reasoning.append(f"Suggestion: {suggestion}")
            else:
                reasoning.append("Please check the logs for details.")
            return QueryResponse(
                answer=f"Error: {error_info.message}",
                citations=[],
                reasoning=reasoning,
                metrics={"error": error_info.message, "error_details": error_data},
            )

    future: asyncio.Future = asyncio.create_task(runner())
    http_request.app.state.async_tasks[task_id] = future
    return {"query_id": task_id}


@router.get("/query/{query_id}", dependencies=[require_permission("query")])
async def get_query_status(query_id: str, request: Request) -> Response:
    future = request.app.state.async_tasks.get(query_id)
    if future is None:
        return JSONResponse({"detail": "not found"}, status_code=404)
    if not future.done():
        return JSONResponse({"status": "running"})
    result = future.result()
    del request.app.state.async_tasks[query_id]
    if isinstance(result, QueryResponse):
        return JSONResponse(result.model_dump())
    return JSONResponse(result)


@router.delete("/query/{query_id}", dependencies=[require_permission("query")])
async def cancel_query(query_id: str, request: Request) -> Response:
    future = request.app.state.async_tasks.get(query_id)
    if future is None:
        return PlainTextResponse("not found", status_code=404)
    future.cancel()
    del request.app.state.async_tasks[query_id]
    return PlainTextResponse("canceled")


@router.get("/metrics", dependencies=[require_permission("metrics")])
async def metrics_endpoint(_: None = None) -> Response:
    """Expose Prometheus metrics."""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/health", dependencies=[require_permission("health")])
def health_endpoint(_: None = None) -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.get("/capabilities", dependencies=[require_permission("capabilities")])
def capabilities_endpoint(_: None = None) -> dict:
    config = get_config()
    reasoning_modes = [m.value for m in ReasoningMode]
    llm_backends = getattr(config, "llm_backends", [])
    storage_info = {
        "ontology": getattr(StorageManager, "has_ontology", lambda: False)(),
        "vector_search": StorageManager.has_vss(),
    }
    search_capabilities = {
        "external_lookup": getattr(config.search, "external_lookup", False),
    }
    agent_info = {
        "synthesizer": {
            "description": "Generates comprehensive answers with citations",
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


@router.get("/config", dependencies=[require_permission("config")])
def get_config_endpoint(_: None = None) -> dict:
    """Return the current configuration."""
    return get_config().model_dump(mode="json")


@router.put("/config", dependencies=[require_permission("config")])
def update_config_endpoint(updates: dict, request: Request, _: None = None) -> dict:
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


@router.post("/config", dependencies=[require_permission("config")])
def replace_config_endpoint(new_config: dict, request: Request, _: None = None) -> dict:
    """Replace the entire configuration at runtime."""
    loader = cast(ConfigLoader, request.app.state.config_loader)
    try:
        new_cfg = ConfigModel(**new_config)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    loader._config = new_cfg
    loader.notify_observers(new_cfg)
    return new_cfg.model_dump(mode="json")


@router.delete("/config", dependencies=[require_permission("config")])
def reload_config_endpoint(request: Request, _: None = None) -> dict:
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
    loader = config_loader or ConfigLoader()
    limiter = limiter or Limiter(key_func=get_remote_address)
    if request_logger is None:
        request_logger = create_request_logger()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        StorageManager.setup()
        watch_ctx = loader.watching()
        watch_ctx.__enter__()
        app.state.watch_ctx = watch_ctx
        try:
            yield
        finally:
            try:
                ctx = getattr(app.state, "watch_ctx", None)
                if ctx is not None:
                    ctx.__exit__(None, None, None)
                    app.state.watch_ctx = None
            finally:
                loader.stop_watching()

    app = FastAPI(
        title="Autoresearch API",
        description="API for interacting with the Autoresearch system",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(AuthMiddleware)

    app.state.limiter = limiter
    app.state.request_logger = request_logger
    app.state.config_loader = loader
    app.state.async_tasks = {}

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

    app.include_router(router)
    app.add_exception_handler(RateLimitExceeded, handle_rate_limit)
    return app


# Default application instance used by the package
app = create_app()
config_loader = cast(ConfigLoader, app.state.config_loader)
limiter = app.state.limiter
