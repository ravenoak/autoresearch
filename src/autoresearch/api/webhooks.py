"""Webhook utilities for the Autoresearch API."""

from __future__ import annotations

import logging
import time

import httpx

from ..models import QueryResponse


log = logging.getLogger(__name__)


def notify_webhook(
    url: str, result: QueryResponse, timeout: float = 5, retries: int = 3, backoff: float = 0.5
) -> None:
    """Send the final result to a webhook URL if configured.

    Webhook delivery is retried ``retries`` times with exponential backoff when
    a request fails or returns a non-2xx response. Failures are logged but do
    not raise exceptions to the caller.
    """

    for attempt in range(retries):
        try:
            resp = httpx.post(url, json=result.model_dump(), timeout=timeout)
            resp.raise_for_status()
            return
        except httpx.RequestError as exc:
            log.warning("Webhook request to %s failed on attempt %s: %s", url, attempt + 1, exc)
            if attempt < retries - 1:
                time.sleep(backoff * 2**attempt)
