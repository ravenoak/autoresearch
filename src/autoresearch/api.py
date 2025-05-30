"""
FastAPI API for Autoresearch.
"""
from fastapi import FastAPI, HTTPException
from .config import ConfigLoader
from .orchestration.orchestrator import Orchestrator
from .models import QueryResponse

app = FastAPI()

@app.post("/query", response_model=QueryResponse)
def query_endpoint(payload: dict):
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="`query` field is required")
    config = ConfigLoader.load_config()
    result = Orchestrator.run_query(query, config)
    return result

