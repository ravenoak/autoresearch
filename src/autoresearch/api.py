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
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)
from .config import ConfigLoader, get_config
from .orchestration.orchestrator import Orchestrator
from .tracing import get_tracer, setup_tracing
from .models import QueryResponse
from .storage import StorageManager
from pydantic import ValidationError

config_loader = ConfigLoader()
app = FastAPI()
_watch_ctx = None


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
def query_endpoint(payload: dict) -> QueryResponse:
    """Process a query and return a structured response.

    This endpoint accepts a JSON payload containing a query string and optional
    configuration parameters. It processes the query using the Orchestrator,
    which coordinates multiple agents to produce an evidence-backed answer.

    The endpoint also supports dynamic configuration by allowing clients to override
    configuration values in the payload. Any key in the payload that matches a
    configuration attribute will be used to update the configuration for this query.

    Args:
        payload (dict): A dictionary containing:
            - query (str): The query string to process (required)
            - Additional key-value pairs for configuration overrides (optional)

    Returns:
        QueryResponse: A structured response containing:
            - answer (str): The synthesized answer to the query
            - citations (list): Evidence supporting the answer
            - reasoning (list): Explanation of the reasoning process
            - metrics (dict): Performance metrics for the query

    Raises:
        HTTPException: If the query field is missing or empty
    """
    query = payload.get("query")
    if not query:
        raise HTTPException(
            status_code=400, detail="`query` field is required"
        )
    config = get_config()

    # Update config with parameters from the payload
    for key, value in payload.items():
        if key != "query" and hasattr(config, key):
            setattr(config, key, value)

    setup_tracing(getattr(config, "tracing_enabled", False))
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("/query"):
        try:
            result = Orchestrator.run_query(query, config)
        except Exception as exc:
            # Create a valid QueryResponse object with error information
            return QueryResponse(
                answer=f"Error: {str(exc)}",
                citations=[],
                reasoning=["An error occurred during processing.", "Please check the logs for details."],
                metrics={"error": str(exc)}
            )
    try:
        validated = (
            result
            if isinstance(result, QueryResponse)
            else QueryResponse.model_validate(result)
        )
    except ValidationError as exc:  # pragma: no cover - should not happen
        # Create a valid QueryResponse object with error information
        return QueryResponse(
            answer=f"Error: Invalid response format",
            citations=[],
            reasoning=["The response format was invalid.", "Please check the logs for details."],
            metrics={"error": str(exc)}
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
