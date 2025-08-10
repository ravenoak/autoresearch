"""Webhook utilities for the Autoresearch API."""

from __future__ import annotations

import logging

import httpx

from ..models import QueryResponse


log = logging.getLogger(__name__)


def notify_webhook(url: str, result: QueryResponse, timeout: float = 5) -> None:
    """Send the final result to a webhook URL if configured."""
    try:
        httpx.post(url, json=result.model_dump(), timeout=timeout)
    except httpx.RequestError as exc:
        log.warning("Webhook request to %s failed: %s", url, exc)
