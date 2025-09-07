"""Streaming endpoints for the Autoresearch API."""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from fastapi.responses import StreamingResponse

from ..config import get_config
from ..error_utils import format_error_for_api, get_error_info
from ..models import QueryRequest, QueryResponse
from ..orchestration import ReasoningMode
from .deps import create_orchestrator
from . import webhooks


# Interval between heartbeat messages to keep connections alive, in seconds.
KEEPALIVE_INTERVAL = 15


async def query_stream_endpoint(request: QueryRequest) -> StreamingResponse:
    """Stream incremental query results as JSON lines.

    A blank line is sent every ``KEEPALIVE_INTERVAL`` seconds to prevent
    intermediaries from closing idle connections. Consumers should ignore
    empty lines. Once processing completes the final response is posted to any
    configured webhooks.
    """
    config = get_config()

    if request.reasoning_mode is not None:
        config.reasoning_mode = ReasoningMode(request.reasoning_mode.value)
    if request.loops is not None:
        config.loops = request.loops
    if request.llm_backend is not None:
        config.llm_backend = request.llm_backend

    queue: asyncio.Queue[str | None] = asyncio.Queue()
    timeout = getattr(config.api, "webhook_timeout", 5)
    retries = getattr(config.api, "webhook_retries", 3)
    backoff = getattr(config.api, "webhook_backoff", 0.5)

    def send_webhooks(response: QueryResponse) -> None:
        if request.webhook_url:
            webhooks.notify_webhook(request.webhook_url, response, timeout, retries, backoff)
        for url in getattr(config.api, "webhooks", []):
            webhooks.notify_webhook(url, response, timeout, retries, backoff)

    def on_cycle_end(loop_idx: int, state) -> None:
        partial = state.synthesize()
        queue.put_nowait(partial.model_dump_json())

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
        queue.put_nowait(None)
        send_webhooks(result)

    asyncio.get_running_loop().run_in_executor(None, run)

    async def generator() -> AsyncGenerator[str, None]:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_INTERVAL)
            except asyncio.TimeoutError:
                # Emit a heartbeat to keep the connection alive.
                yield "\n"
                continue
            if item is None:
                break
            yield item + "\n"

    return StreamingResponse(generator(), media_type="application/json")
