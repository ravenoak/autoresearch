"""LLM adapter implementations for various backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
import os
import requests


class LLMAdapter(ABC):
    """Abstract LLM adapter interface."""

    @abstractmethod
    def generate(
        self, prompt: str, model: str | None = None, **kwargs: Any
    ) -> str:
        """Generate text from the given prompt using the specified model."""


class DummyAdapter(LLMAdapter):
    """Simple adapter used for testing."""

    def generate(
        self, prompt: str, model: str | None = None, **kwargs: Any
    ) -> str:
        return f"Dummy response for {prompt}"


class LMStudioAdapter(LLMAdapter):
    """Adapter for the LM Studio local API."""

    def __init__(self) -> None:
        # Allow custom endpoint via env for tests/config
        self.endpoint = os.getenv(
            "LMSTUDIO_ENDPOINT", "http://localhost:1234/v1/chat/completions"
        )

    def generate(
        self, prompt: str, model: str | None = None, **kwargs: Any
    ) -> str:
        payload = {
            "model": model or "lmstudio",
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = requests.post(self.endpoint, json=payload, timeout=30)
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
        return str(
            data.get("choices", [{}])[0].get("message", {}).get("content", "")
        )


class OpenAIAdapter(LLMAdapter):
    """Adapter for the OpenAI API using raw HTTP calls."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.endpoint = os.getenv(
            "OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions"
        )

    def generate(
        self, prompt: str, model: str | None = None, **kwargs: Any
    ) -> str:
        payload = {
            "model": model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        resp = requests.post(
            self.endpoint, json=payload, headers=headers, timeout=30
        )
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
        return str(
            data.get("choices", [{}])[0].get("message", {}).get("content", "")
        )
