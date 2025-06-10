"""LLM adapter implementations for various backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
import requests


class LLMAdapter(ABC):
    """Abstract LLM adapter interface."""

    @abstractmethod
    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        """Generate text from the given prompt using the specified model."""


class DummyAdapter(LLMAdapter):
    """Simple adapter used for testing."""

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        return f"Dummy response for {prompt}"


class LMStudioAdapter(LLMAdapter):
    """Adapter for the LM Studio local API."""

    endpoint: str = "http://localhost:1234/v1/chat/completions"

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        payload = {
            "model": model or "lmstudio",
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            resp = requests.post(self.endpoint, json=payload, timeout=30)
            resp.raise_for_status()
            data: Dict[str, Any] = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as exc:  # pragma: no cover - network errors
            return f"Error: {exc}"


class OpenAIAdapter(LLMAdapter):
    """Adapter for the OpenAI API."""

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        import openai

        response = openai.ChatCompletion.create(
            model=model or "gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message["content"]
