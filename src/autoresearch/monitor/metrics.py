"""Prometheus metrics endpoint for the monitoring server."""

from __future__ import annotations

from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


async def metrics_endpoint(_: None = None) -> PlainTextResponse:
    """Return current metrics in Prometheus text format.

    Returns:
        PlainTextResponse: Prometheus metrics with ``200`` status code.
    """

    payload = generate_latest()
    if isinstance(payload, bytes):
        body = payload.decode("utf-8", "replace")
    else:  # pragma: no cover - defensive fallback
        body = str(payload)
    return PlainTextResponse(
        body,
        media_type=CONTENT_TYPE_LATEST,
        status_code=200,
    )


__all__ = ["metrics_endpoint"]
