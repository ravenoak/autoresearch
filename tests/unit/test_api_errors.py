from fastapi import Request
from fastapi.responses import PlainTextResponse

from autoresearch.api import errors, middleware


def _req() -> Request:
    return Request(scope={"type": "http", "client": ("test", 0)})


def test_handle_rate_limit_response(monkeypatch):
    resp = PlainTextResponse("x", status_code=429)
    monkeypatch.setattr(middleware, "_rate_limit_exceeded_handler", lambda r, e: resp)
    assert errors.handle_rate_limit(_req(), Exception("boom")) is resp


def test_handle_rate_limit_text(monkeypatch):
    monkeypatch.setattr(middleware, "_rate_limit_exceeded_handler", lambda r, e: "oops")
    result = errors.handle_rate_limit(_req(), Exception("fail"))
    assert isinstance(result, PlainTextResponse)
    assert result.body.decode() == "oops"
    assert result.status_code == 429
