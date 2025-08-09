"""Webhook utilities for the Autoresearch API."""

from __future__ import annotations

import httpx

from ..models import QueryResponse


def notify_webhook(url: str, result: QueryResponse, timeout: float = 5) -> None:
    """Send the final result to a webhook URL if configured."""
    try:
        httpx.post(url, json=result.model_dump(), timeout=timeout)
    except Exception:
        # pragma: no cover - ignore webhook errors
        pass
