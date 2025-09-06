from __future__ import annotations

from .test_api_auth import _setup


def test_auth_validated_before_body(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"

    resp = api_client.post("/query", data="not json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing API key"


def test_webhook_auth(monkeypatch, api_client):
    cfg = _setup(monkeypatch)
    cfg.api.api_key = "secret"
    called: list[str] = []
    monkeypatch.setattr(
        "autoresearch.api.webhooks.notify_webhook",
        lambda url, result, timeout=5, retries=3, backoff=0.5: called.append(url),
    )

    resp = api_client.post(
        "/query",
        json={"query": "q", "webhook_url": "http://example.com"},
        headers={"X-API-Key": "secret"},
    )
    assert resp.status_code == 200
    assert called == ["http://example.com"]

    called.clear()
    resp_bad = api_client.post(
        "/query",
        json={"query": "q", "webhook_url": "http://example.com"},
    )
    assert resp_bad.status_code == 401
    assert called == []
