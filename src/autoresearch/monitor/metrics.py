"""Prometheus metrics endpoint for the monitoring server."""

from __future__ import annotations

from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


def metrics_endpoint(_: None = None) -> PlainTextResponse:
    """Return current metrics in Prometheus text format."""

    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


__all__ = ["metrics_endpoint"]
