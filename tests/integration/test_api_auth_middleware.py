# mypy: ignore-errors
from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from requests import Response as HTTPResponse

from autoresearch.models import QueryResponse

from .test_api_auth import _setup


def test_auth_validated_before_body(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    client = cast(Any, api_client)

    resp = cast(
        HTTPResponse,
        client.post(
            "/query",
            content="not json",
            headers={"Content-Type": "application/json"},
        ),
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing API key"


def test_invalid_key_before_body(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    client = cast(Any, api_client)

    resp = cast(
        HTTPResponse,
        client.post(
            "/query",
            content="not json",
            headers={"Content-Type": "application/json", "X-API-Key": "bad"},
        ),
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid API key"


def test_webhook_auth(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient
) -> None:
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    called: list[str] = []

    def _notify_webhook(
        url: str,
        result: QueryResponse,
        timeout: float = 5,
        retries: int = 3,
        backoff: float = 0.5,
    ) -> None:
        called.append(url)

    monkeypatch.setattr("autoresearch.api.webhooks.notify_webhook", _notify_webhook)

    client = cast(Any, api_client)

    resp = cast(
        HTTPResponse,
        client.post(
            "/query",
            json={"query": "q", "webhook_url": "http://example.com"},
            headers={"X-API-Key": "secret"},
        ),
    )
    assert resp.status_code == 200
    assert called == ["http://example.com"]

    called.clear()
    resp_bad = cast(
        HTTPResponse,
        client.post(
            "/query",
            json={"query": "q", "webhook_url": "http://example.com"},
        ),
    )
    assert resp_bad.status_code == 401
    assert called == []
