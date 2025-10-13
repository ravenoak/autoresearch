"""Regression tests for the LM Studio adapter."""

from __future__ import annotations

from typing import Any

import pytest
import requests
from requests import Response
from requests.exceptions import HTTPError

from autoresearch.errors import LLMError
from autoresearch.llm.adapters import LMStudioAdapter


class _DummySession:
    """Simple stand-in for a requests session."""

    def __init__(self, side_effect: Exception | None = None, payload: str | None = None) -> None:
        self.side_effect = side_effect
        self.payload = payload or "Hello from LM Studio"

    def post(self, endpoint: str, json: dict[str, Any], timeout: float) -> Response:
        if self.side_effect:
            raise self.side_effect
        response = Response()
        response.status_code = 200
        response._content = (  # type: ignore[attr-defined]
            f'{{"choices": [{{"message": {{"content": "{self.payload}"}}}}]}}'.encode("utf-8")
        )
        return response


def test_lmstudio_adapter_passes_through_model_identifier() -> None:
    """Model identifiers should not be restricted to the static allowlist."""

    adapter = LMStudioAdapter()
    assert adapter.validate_model("qwen/qwen3-4b-2507") == "qwen/qwen3-4b-2507"


def test_lmstudio_adapter_timeout_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Timeout should be configurable via environment variables with graceful fallback."""

    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "42.5")
    adapter = LMStudioAdapter()
    assert pytest.approx(getattr(adapter, "timeout")) == 42.5

    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "invalid")
    adapter = LMStudioAdapter()
    assert pytest.approx(getattr(adapter, "timeout")) == 300.0


def test_lmstudio_adapter_http_error_surfaces_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP errors should be wrapped with actionable metadata for diagnostics."""

    response = Response()
    response.status_code = 400
    response._content = b"Bad Request"  # type: ignore[attr-defined]
    error = HTTPError("bad request")
    error.response = response
    monkeypatch.setattr(
        "autoresearch.llm.adapters.get_session",
        lambda: _DummySession(side_effect=error),
    )

    adapter = LMStudioAdapter()
    with pytest.raises(LLMError) as excinfo:
        adapter.generate("test prompt", model="qwen/qwen3-4b-2507")

    err = excinfo.value
    assert err.context["metadata"]["status_code"] == 400
    assert "Inspect LM Studio server logs" in err.context["suggestion"]


def test_lmstudio_adapter_request_exception_has_default_suggestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-HTTP request failures should fall back to the connectivity hint."""

    monkeypatch.setattr(
        "autoresearch.llm.adapters.get_session",
        lambda: _DummySession(
            side_effect=requests.exceptions.ConnectionError("disconnected")
        ),
    )

    adapter = LMStudioAdapter()
    with pytest.raises(LLMError) as excinfo:
        adapter.generate("prompt")

    assert "Ensure LM Studio is running" in excinfo.value.context["suggestion"]
