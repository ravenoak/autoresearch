import logging
import time
from types import SimpleNamespace

import httpx

from autoresearch.api.webhooks import notify_webhook
from autoresearch.models import QueryResponse
import pytest


def test_notify_webhook_logs_request_error(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    def raise_error(*args, **kwargs):
        raise httpx.RequestError("boom", request=httpx.Request("POST", "http://hook"))

    monkeypatch.setattr(httpx, "post", raise_error)

    payload = QueryResponse(answer="", citations=[], reasoning=[], metrics={})
    with caplog.at_level(logging.WARNING):
        notify_webhook("http://hook", payload)

    assert any(
        "http://hook" in record.getMessage() and "boom" in record.getMessage()
        for record in caplog.records
    )


def test_notify_webhook_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Webhook delivery retries with exponential backoff."""
    calls = {"count": 0}

    def fake_post(url, json, timeout):
        if calls["count"] < 2:
            calls["count"] += 1
            raise httpx.RequestError("fail", request=httpx.Request("POST", url))
        calls["count"] += 1
        return SimpleNamespace(raise_for_status=lambda: None)

    sleeps: list[float] = []

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))

    payload = QueryResponse(answer="", citations=[], reasoning=[], metrics={})
    notify_webhook("http://hook", payload, timeout=1, retries=3, backoff=0.5)

    assert calls["count"] == 3
    assert sleeps == [0.5, 1.0]
