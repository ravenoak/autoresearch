"""LLM adapter implementations for various backends.

This module provides adapter classes that interface with different LLM providers.
It includes a base abstract adapter class and concrete implementations for:
- DummyAdapter: A simple adapter used for testing
- LMStudioAdapter: An adapter for the LM Studio local API
- OpenAIAdapter: An adapter for the OpenAI API

Each adapter implements a common interface for generating text from prompts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
import os
import requests


class LLMAdapter(ABC):
    """Abstract LLM adapter interface."""

    # Class variable to store available models for each adapter
    available_models: list[str] = []

    @classmethod
    def get_adapter(cls, name: str) -> "LLMAdapter":
        """Get an adapter instance by name.

        Args:
            name: The name of the adapter to retrieve

        Returns:
            An instance of the requested LLM adapter
        """
        from .registry import LLMFactory
        return LLMFactory.get(name)

    def validate_model(self, model: str | None) -> str:
        """Validate the model and return the model name to use.

        Args:
            model: The model name to validate, or None to use the default

        Returns:
            A valid model name to use

        Raises:
            LLMError: If the model is invalid and no default is available
        """
        from ..errors import LLMError

        if model is None:
            # Use default model if none specified
            return self.available_models[0] if self.available_models else "default"

        if not self.available_models or model in self.available_models:
            return model

        raise LLMError(
            f"Invalid model: {model}",
            available_models=self.available_models,
            provided=model,
            suggestion=f"Configure a valid model in your configuration file. Available models: {', '.join(self.available_models)}"
        )

    @abstractmethod
    def generate(
        self, prompt: str, model: str | None = None, **kwargs: Any
    ) -> str:
        """Generate text from the given prompt using the specified model.

        Args:
            prompt: The prompt to generate text from
            model: Optional model name to use, defaults to the first available model
            **kwargs: Additional arguments to pass to the underlying LLM

        Returns:
            The generated text response
        """


class DummyAdapter(LLMAdapter):
    """Simple adapter used for testing."""

    available_models = ["dummy-model"]

    def generate(
        self, prompt: str, model: str | None = None, **kwargs: Any
    ) -> str:
        """Generate a dummy response for testing purposes.

        Args:
            prompt: The prompt to generate text from
            model: Optional model name to use, defaults to "dummy-model"
            **kwargs: Additional arguments (ignored in this adapter)

        Returns:
            A dummy response string containing the prompt and model
        """
        model = self.validate_model(model)
        return f"Dummy response for {prompt} using {model}"


class LMStudioAdapter(LLMAdapter):
    """Adapter for the LM Studio local API."""

    available_models = ["lmstudio", "llama2", "mistral", "mixtral"]

    def __init__(self) -> None:
        """Initialize the LM Studio adapter.

        The endpoint can be customized using the LMSTUDIO_ENDPOINT environment variable.
        """
        # Allow custom endpoint via env for tests/config
        self.endpoint = os.getenv(
            "LMSTUDIO_ENDPOINT", "http://localhost:1234/v1/chat/completions"
        )

    def generate(
        self, prompt: str, model: str | None = None, **kwargs: Any
    ) -> str:
        """Generate text using the LM Studio local API.

        Args:
            prompt: The prompt to generate text from
            model: Optional model name to use, defaults to the first available model
            **kwargs: Additional arguments to pass to the API

        Returns:
            The generated text response

        Raises:
            LLMError: If there's an error communicating with the LM Studio API
        """
        model = self.validate_model(model)

        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            resp = requests.post(self.endpoint, json=payload, timeout=30)
            resp.raise_for_status()
            data: Dict[str, Any] = resp.json()
            return str(
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
        except requests.RequestException as e:
            from ..errors import LLMError
            raise LLMError(
                f"Failed to generate response from LM Studio",
                cause=e,
                model=model,
                suggestion="Ensure LM Studio is running and accessible at the configured endpoint"
            )


class OpenAIAdapter(LLMAdapter):
    """Adapter for the OpenAI API using raw HTTP calls."""

    available_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]

    def __init__(self) -> None:
        """Initialize the OpenAI adapter.

        The API key is read from the OPENAI_API_KEY environment variable.
        The endpoint can be customized using the OPENAI_ENDPOINT environment variable.
        """
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.endpoint = os.getenv(
            "OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions"
        )

    def generate(
        self, prompt: str, model: str | None = None, **kwargs: Any
    ) -> str:
        """Generate text using the OpenAI API.

        Args:
            prompt: The prompt to generate text from
            model: Optional model name to use, defaults to the first available model
            **kwargs: Additional arguments to pass to the API

        Returns:
            The generated text response

        Raises:
            LLMError: If the API key is missing or there's an error communicating with the OpenAI API
        """
        model = self.validate_model(model)

        if not self.api_key:
            from ..errors import LLMError
            raise LLMError(
                "OpenAI API key not found",
                model=model,
                suggestion="Set the OPENAI_API_KEY environment variable with your API key"
            )

        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.post(
                self.endpoint, json=payload, headers=headers, timeout=30
            )
            resp.raise_for_status()
            data: Dict[str, Any] = resp.json()
            return str(
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
        except requests.RequestException as e:
            from ..errors import LLMError
            raise LLMError(
                f"Failed to generate response from OpenAI API",
                cause=e,
                model=model,
                suggestion="Check your API key and internet connection, or try a different model"
            )
