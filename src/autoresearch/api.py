"""
FastAPI API for Autoresearch.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from .config import get_config
from .orchestration.orchestrator import Orchestrator
from .models import QueryResponse

app = FastAPI()


@app.post("/query", response_model=QueryResponse)
def query_endpoint(payload: dict):
    query = payload.get("query")
    if not query:
        raise HTTPException(
            status_code=400, detail="`query` field is required"
        )
    config = get_config()
    result = Orchestrator.run_query(query, config)
    return result


@app.get("/metrics")
def metrics_endpoint() -> PlainTextResponse:
    """Expose Prometheus metrics."""
    data = generate_latest()
    return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)
