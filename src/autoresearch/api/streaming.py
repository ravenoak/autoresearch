"""Streaming endpoints for the Autoresearch API."""

from __future__ import annotations

import asyncio

from fastapi.responses import StreamingResponse

from ..config import get_config
from ..error_utils import format_error_for_api, get_error_info
from ..models import QueryRequest, QueryResponse
from ..orchestration import ReasoningMode
from .deps import create_orchestrator
from .webhooks import notify_webhook


async def query_stream_endpoint(request: QueryRequest) -> StreamingResponse:
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
            result = create_orchestrator().run_query(
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
            notify_webhook(request.webhook_url, result, timeout)
        for url in getattr(config.api, "webhooks", []):
            notify_webhook(url, result, timeout)
        queue.put_nowait(None)

    asyncio.get_running_loop().run_in_executor(None, run)

    async def generator():
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item + "\n"

    return StreamingResponse(generator(), media_type="application/json")
