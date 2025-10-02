from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
import requests

from autoresearch.errors import LLMError
from autoresearch.llm import adapters
from autoresearch.typing.http import RequestsAdapterProtocol, RequestsSessionProtocol


class RecordingResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.raise_called = False
        self._headers: dict[str, str] = {}
        self.status_code = 200

    def json(self, **kwargs: Any) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        self.raise_called = True

    @property
    def headers(self) -> dict[str, str]:
        return self._headers


class DummyAdapter:
    """Minimal adapter implementation satisfying ``RequestsAdapterProtocol``."""

    def close(self) -> None:  # pragma: no cover - no resources to release
        return None


class RecordingSession(RequestsSessionProtocol):
    def __init__(self, response: RecordingResponse) -> None:
        self._response = response
        self.mounted: list[tuple[str, object]] = []
        self.requests: list[tuple[str, str, dict[str, Any]]] = []
        self._headers: dict[str, str] = {}
        self._adapters: list[tuple[str, RequestsAdapterProtocol]] = []
        self._default_adapter: RequestsAdapterProtocol = DummyAdapter()

    def mount(self, prefix: str, adapter: RequestsAdapterProtocol) -> None:
        self.mounted.append((prefix, adapter))
        self._adapters.append((prefix, adapter))

    def get_adapter(self, url: str) -> RequestsAdapterProtocol:
        for prefix, adapter in reversed(self._adapters):
            if url.startswith(prefix):
                return adapter
        return self._adapters[-1][1] if self._adapters else self._default_adapter

    def close(self) -> None:
        pass

    @property
    def headers(self) -> dict[str, str]:
        return self._headers

    def request(self, method: str, url: str, *args: Any, **kwargs: Any) -> RecordingResponse:
        self.requests.append((method, url, kwargs))
        return self._response

    def get(self, url: str, *args: Any, **kwargs: Any) -> RecordingResponse:
        return self.request("GET", url, *args, **kwargs)

    def post(self, url: str, *args: Any, **kwargs: Any) -> RecordingResponse:
        return self.request("POST", url, *args, **kwargs)


AdapterFactory = Callable[[], adapters.LLMAdapter]


@pytest.mark.parametrize(
    ("adapter_cls", "env"),
    [
        (adapters.LMStudioAdapter, {}),
        (adapters.OpenAIAdapter, {"OPENAI_API_KEY": "sk-test"}),
        (adapters.OpenRouterAdapter, {"OPENROUTER_API_KEY": "or-test"}),
    ],
)
def test_adapter_generate_invokes_raise_for_status(
    monkeypatch: pytest.MonkeyPatch,
    adapter_cls: type[adapters.LLMAdapter],
    env: dict[str, str],
) -> None:
    """Adapters use the shared session and trigger response validation."""

    payload = {"choices": [{"message": {"content": "ok"}}]}
    response = RecordingResponse(payload)
    session = RecordingSession(response)
    assert isinstance(session, RequestsSessionProtocol)
    monkeypatch.setattr(adapters, "get_session", lambda: session)

    for key, value in env.items():
        monkeypatch.setenv(key, value)

    adapter = adapter_cls()
    result = adapter.generate("prompt")

    assert response.raise_called is True
    assert "ok" in result
    assert session.requests


@pytest.mark.parametrize(
    "adapter_factory",
    [
        lambda: adapters.LMStudioAdapter(),
        lambda: adapters.OpenAIAdapter(),
        lambda: adapters.OpenRouterAdapter(),
    ],
)
def test_adapter_generate_wraps_request_exceptions(
    monkeypatch: pytest.MonkeyPatch, adapter_factory: AdapterFactory
) -> None:
    """Network failures surface as LLMError with preserved context."""

    def boom(*args: Any, **kwargs: Any) -> RecordingResponse:  # pragma: no cover - type stub
        raise requests.RequestException("boom")

    class FailingSession(RequestsSessionProtocol):
        def __init__(self) -> None:
            self._headers: dict[str, str] = {}
            self._adapters: list[tuple[str, RequestsAdapterProtocol]] = []
            self._default_adapter: RequestsAdapterProtocol = DummyAdapter()

        def post(self, *args: Any, **kwargs: Any) -> RecordingResponse:
            return boom(*args, **kwargs)

        def mount(
            self, prefix: str, adapter: RequestsAdapterProtocol
        ) -> None:  # pragma: no cover - not invoked
            self._adapters.append((prefix, adapter))

        def close(self) -> None:  # pragma: no cover - not invoked
            return None

        def get(self, *args: Any, **kwargs: Any) -> RecordingResponse:  # pragma: no cover - type stub
            return boom(*args, **kwargs)

        def request(self, *args: Any, **kwargs: Any) -> RecordingResponse:  # pragma: no cover - type stub
            return boom(*args, **kwargs)

        def get_adapter(self, url: str) -> RequestsAdapterProtocol:
            for prefix, adapter in reversed(self._adapters):
                if url.startswith(prefix):  # pragma: no cover - not used in tests
                    return adapter
            return self._adapters[-1][1] if self._adapters else self._default_adapter

        @property
        def headers(self) -> dict[str, str]:
            return self._headers

    session: RequestsSessionProtocol = FailingSession()
    monkeypatch.setattr(adapters, "get_session", lambda: session)
    monkeypatch.setenv("OPENAI_API_KEY", "token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "token")

    adapter = adapter_factory()

    with pytest.raises(LLMError):
        adapter.generate("prompt")


@pytest.mark.parametrize(
    "adapter_factory",
    [
        adapters.OpenAIAdapter,
        adapters.OpenRouterAdapter,
    ],
)
def test_adapter_requires_api_key(
    monkeypatch: pytest.MonkeyPatch, adapter_factory: type[adapters.LLMAdapter]
) -> None:
    """Adapters validate API keys before performing network calls."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def _unexpected_session() -> RequestsSessionProtocol:  # pragma: no cover - fail fast
        raise AssertionError("Session should not be requested without credentials")

    monkeypatch.setattr(adapters, "get_session", _unexpected_session)

    adapter = adapter_factory()

    with pytest.raises(LLMError):
        adapter.generate("prompt")
