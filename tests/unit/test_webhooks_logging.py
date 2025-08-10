import logging

import httpx

from autoresearch.api.webhooks import notify_webhook
from autoresearch.models import QueryResponse


def test_notify_webhook_logs_request_error(monkeypatch, caplog):
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
