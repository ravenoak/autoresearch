"""
FastAPI API for Autoresearch.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from .config import ConfigLoader, get_config
from .orchestration.orchestrator import Orchestrator
from .tracing import get_tracer, setup_tracing
from .models import QueryResponse
from pydantic import ValidationError

config_loader = ConfigLoader()
app = FastAPI()

# Start watching the main configuration file so that changes
# to ``autoresearch.toml`` are picked up while the API is running.
config_loader.watch_changes()


@app.on_event("shutdown")
def _stop_config_watcher() -> None:
    """Stop the configuration watcher thread when the app shuts down."""
    config_loader.stop_watching()


@app.post("/query", response_model=QueryResponse)
def query_endpoint(payload: dict):
    query = payload.get("query")
    if not query:
        raise HTTPException(
            status_code=400, detail="`query` field is required"
        )
    config = get_config()
    setup_tracing(getattr(config, "tracing_enabled", False))
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("/query"):
        result = Orchestrator.run_query(query, config)
    try:
        validated = (
            result
            if isinstance(result, QueryResponse)
            else QueryResponse.model_validate(result)
        )
    except ValidationError as exc:  # pragma: no cover - should not happen
        raise HTTPException(
            status_code=500, detail="Invalid response format"
        ) from exc
    return validated


@app.get("/metrics")
def metrics_endpoint() -> PlainTextResponse:
    """Expose Prometheus metrics."""
    data = generate_latest()
    return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)
