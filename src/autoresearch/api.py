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

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)
from .config import ConfigLoader, get_config
from .orchestration.orchestrator import Orchestrator
from .tracing import get_tracer, setup_tracing
from .models import QueryRequest, QueryResponse
from .storage import StorageManager
from pydantic import ValidationError
from .error_utils import get_error_info, format_error_for_api

config_loader = ConfigLoader()
app = FastAPI(
    title="Autoresearch API",
    description="API for interacting with the Autoresearch system",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)
_watch_ctx = None


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

        No authentication is required for local usage. For remote usage, implement your own authentication
        mechanism in front of this API.

        ## Rate Limiting

        No rate limiting is implemented by default. For production usage, consider implementing rate
        limiting in front of this API.

        ## Endpoints

        - **POST /query**: Submit a query to the Autoresearch system
        - **GET /metrics**: Retrieve Prometheus metrics for monitoring
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


@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest) -> QueryResponse:
    """Process a query and return a structured response.

    This endpoint accepts a JSON payload containing a query string and optional
    configuration parameters. It processes the query using the Orchestrator,
    which coordinates multiple agents to produce an evidence-backed answer.

    The endpoint also supports dynamic configuration by allowing clients to override
    configuration values in the payload. Any key in the payload that matches a
    configuration attribute will be used to update the configuration for this query.

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

    # Update config with parameters from the request
    if request.reasoning_mode is not None:
        config.reasoning_mode = request.reasoning_mode
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
            return QueryResponse(
                answer=f"Error: {error_info.message}",
                citations=[],
                reasoning=reasoning,
                metrics={"error": error_info.message, "error_details": error_data},
            )
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
        return QueryResponse(
            answer="Error: Invalid response format",
            citations=[],
            reasoning=reasoning,
            metrics={
                "error": "Invalid response format",
                "validation_error": str(exc),
                "error_details": error_data,
            },
        )
    return validated


@app.get("/metrics")
def metrics_endpoint() -> PlainTextResponse:
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


@app.get("/capabilities")
def capabilities_endpoint() -> dict:
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
    from .llm.adapters import get_available_adapters

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
