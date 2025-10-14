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
import re
import time

import requests

from ..logging_utils import get_logger
from ..typing.http import RequestsResponseProtocol, RequestsSessionProtocol
from .pool import get_session

logger = get_logger(__name__)


class LLMAdapter(ABC):
    """Abstract LLM adapter interface."""

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

    @property
    def available_models(self) -> list[str]:
        """Return the list of available models for this adapter.

        Returns:
            List of available model names
        """
        # Default implementation returns empty list - subclasses should override
        return []

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
            available = self.available_models
            return available[0] if available else "default"

        available = self.available_models
        if not available or model in available:
            return model

        raise LLMError(
            f"Invalid model: {model}",
            available_models=available,
            provided=model,
            suggestion=f"Configure a valid model in your configuration file. Available models: {', '.join(available)}",
        )

    @abstractmethod
    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
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

    @property
    def available_models(self) -> list[str]:
        """Return available models for the dummy adapter."""
        return ["dummy-model"]

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
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
    """Adapter for the LM Studio local API with dynamic model discovery and context size awareness."""

    # Default fallback models when discovery fails
    _fallback_models = ["lmstudio", "llama2", "mistral", "mixtral"]

    # Context size estimates for different model families (conservative estimates)
    _default_context_sizes = {
        # Small models (typically 4-8B parameters)
        "4b": 4096,
        "7b": 4096,
        "8b": 8192,
        "13b": 4096,
        # Medium models (typically 30-36B parameters)
        "30b": 8192,
        "32b": 8192,
        "36b": 16384,
        # Large models (typically 70B+ parameters)
        "70b": 4096,
        "72b": 4096,
        # Qwen models tend to have good context windows
        "qwen": 8192,
        "qwen2": 32768,
        "qwen3": 32768,
        # DeepSeek models
        "deepseek": 32768,
        # Mistral models
        "mistral": 8192,
        "mixtral": 32768,
        # Code models might have smaller contexts
        "code": 4096,
        "coder": 4096,
        # Default conservative estimate
        "default": 4096,
    }

    def __init__(self) -> None:
        """Initialize the LM Studio adapter with context size awareness.

        The endpoint can be customized using the LMSTUDIO_ENDPOINT environment variable.
        The adapter will attempt to discover available models and estimate their context sizes.
        """
        # Allow custom endpoint via env for tests/config
        self.endpoint = os.getenv(
            "LMSTUDIO_ENDPOINT", "http://localhost:1234/v1/chat/completions"
        )
        timeout_env = os.getenv("LMSTUDIO_TIMEOUT")
        try:
            self.timeout = float(timeout_env) if timeout_env else 300.0
        except (TypeError, ValueError):  # pragma: no cover - defensive
            self.timeout = 300.0

        # Initialize available models - will be populated by model discovery
        self._discovered_models: list[str] = []
        self._model_discovery_error: str | None = None
        self._model_context_sizes: dict[str, int] = {}
        self._context_warnings: dict[str, str] = {}
        self._token_usage_history: dict[str, list[int]] = {}  # Track token usage per model
        self._performance_metrics: dict[str, dict[str, float]] = {}  # Track performance metrics
        self._discover_available_models()

    @property
    def available_models(self) -> list[str]:
        """Return available models, preferring discovered models over fallbacks."""
        if self._discovered_models:
            return self._discovered_models
        elif self._model_discovery_error:
            # Return fallbacks when discovery failed but provide warning
            return self._fallback_models
        else:
            # During initialization or when no discovery occurred, return fallbacks
            return self._fallback_models

    def _discover_available_models(self) -> None:
        """Discover available models from LM Studio API and their actual context sizes.

        This method attempts to query the LM Studio API for available models.
        It first queries /v1/models to get the list of loaded models, then for each model,
        it queries /api/v0/models/{model} to get the actual max_context_length.
        If API calls fail, it falls back to heuristic estimation.
        """
        try:
            # Step 1: Get list of models via OpenAI-compatible endpoint
            models_endpoint = self.endpoint.replace("/chat/completions", "/models")
            session: RequestsSessionProtocol = get_session()
            resp: RequestsResponseProtocol = session.get(models_endpoint, timeout=10.0)
            resp.raise_for_status()

            data: Dict[str, Any] = resp.json()
            models = data.get("data", [])

            # Extract model identifiers
            discovered = []
            for model in models:
                model_id = model.get("id") or model.get("model")
                if model_id:
                    discovered.append(model_id)

            if not discovered:
                self._model_discovery_error = "No models found in LM Studio API response"
                return

            # Step 2: Query each model for actual context size
            self._discovered_models = discovered
            for model_id in discovered:
                context_size = self._query_model_context_size(model_id)
                self._model_context_sizes[model_id] = context_size

        except requests.exceptions.RequestException as exc:
            self._model_discovery_error = f"Failed to discover models from LM Studio: {exc}"
            self._fallback_to_heuristic_models()
        except Exception as exc:
            self._model_discovery_error = f"Unexpected error during model discovery: {exc}"
            self._fallback_to_heuristic_models()

    def _query_model_context_size(self, model_id: str) -> int:
        """Query LM Studio API for actual context size of a specific model.

        Args:
            model_id: The model identifier to query

        Returns:
            The actual context size from API, or heuristic estimate if API fails
        """
        try:
            # Query LM Studio-specific endpoint for detailed model info
            base_url = self.endpoint.rsplit('/v1/', 1)[0]  # Remove /v1/chat/completions
            api_endpoint = f"{base_url}/api/v0/models/{model_id}"
            session: RequestsSessionProtocol = get_session()
            resp: RequestsResponseProtocol = session.get(api_endpoint, timeout=10.0)
            resp.raise_for_status()

            model_info: Dict[str, Any] = resp.json()

            # Extract max_context_length if available
            if "max_context_length" in model_info:
                context_size = model_info["max_context_length"]
                logger = get_logger(__name__)
                logger.debug(f"Model {model_id}: context_size={context_size} (from API)")
                return int(context_size)

        except Exception as e:
            logger = get_logger(__name__)
            logger.debug(f"Failed to query context size for {model_id} from API: {e}")

        # Fall back to heuristic estimation
        return self._estimate_context_size(model_id)

    def _fallback_to_heuristic_models(self) -> None:
        """Fall back to using default fallback models when discovery fails."""
        # Use fallback models with default context sizes
        for model in self._fallback_models:
            self._model_context_sizes[model] = self._estimate_context_size(model)
        # Don't set discovered_models to fallbacks - use empty list to indicate no real discovery
        self._discovered_models = []

    def _estimate_context_size(self, model_id: str) -> int:
        """Estimate context size for a model based on its name and known characteristics.

        Args:
            model_id: The model identifier to estimate context size for

        Returns:
            Estimated context size in tokens (conservative estimate)
        """
        model_lower = model_id.lower()

        # Check for specific patterns in model names
        for pattern, context_size in self._default_context_sizes.items():
            if pattern in model_lower:
                return context_size

        # Special handling for some known models
        if "qwen3" in model_lower and "thinking" in model_lower:
            return 8192  # Qwen3 thinking models might have smaller contexts

        if "embedding" in model_lower or "nomic" in model_lower:
            return 512  # Embedding models typically have very small contexts

        # Default conservative estimate
        return self._default_context_sizes["default"]

    def get_context_size(self, model: str) -> int:
        """Get the estimated context size for a model.

        Args:
            model: The model identifier

        Returns:
            Estimated context size in tokens
        """
        return self._model_context_sizes.get(model, self._default_context_sizes["default"])

    def estimate_prompt_tokens(self, prompt: str) -> int:
        """Estimate the number of tokens in a prompt using accurate counting when available.

        Args:
            prompt: The prompt text to estimate tokens for

        Returns:
            Estimated token count using best available method
        """
        from .token_counting import count_tokens_accurate
        return count_tokens_accurate(prompt, self.validate_model(None), "lmstudio")

    def truncate_prompt(self, prompt: str, model: str, max_tokens: int | None = None) -> str:
        """Truncate a prompt to fit within context size limits using intelligent truncation.

        Args:
            prompt: The prompt to truncate
            model: The model identifier to get context size for
            max_tokens: Optional maximum tokens to allow (overrides model context)

        Returns:
            Truncated prompt that should fit within context limits
        """
        if max_tokens is None:
            max_tokens = self.get_context_size(model)

        # Reserve tokens for response generation (rough estimate)
        reserved_for_response = min(512, max_tokens // 4)
        available_for_prompt = max_tokens - reserved_for_response

        estimated_tokens = self.estimate_prompt_tokens(prompt)

        if estimated_tokens <= available_for_prompt:
            return prompt

        # Use intelligent truncation that preserves important content
        return self._intelligently_truncate_prompt(prompt, available_for_prompt)

    def _intelligently_truncate_prompt(self, prompt: str, max_tokens: int) -> str:
        """Intelligently truncate a prompt to preserve the most important content.

        Args:
            prompt: The prompt to truncate
            max_tokens: Maximum tokens to allow

        Returns:
            Intelligently truncated prompt
        """
        # Use conservative character estimate (3 chars per token)
        max_chars = max_tokens * 3

        if len(prompt) <= max_chars:
            return prompt

        # Try to truncate at sentence boundaries first
        sentences = re.split(r'[.!?]+', prompt)
        current_prompt = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add the sentence with its punctuation
            test_prompt = current_prompt + sentence + ". "

            if self.estimate_prompt_tokens(test_prompt) <= max_tokens:
                current_prompt = test_prompt
            else:
                # If adding this sentence would exceed the limit, stop here
                break

        if current_prompt:
            truncated = current_prompt.rstrip() + "... [content truncated to fit context]"
        else:
            # Fallback to simple character truncation
            truncated = prompt[:max_chars] + "... [prompt truncated to fit context]"

        return truncated

    def _generate_context_size_suggestion(self, model: str, context_size: int, prompt_tokens: int) -> str:
        """Generate intelligent suggestions for context size errors.

        Args:
            model: The model identifier
            context_size: The model's context size
            prompt_tokens: Estimated tokens in the prompt

        Returns:
            Intelligent suggestion string for handling context size errors
        """
        suggestions = []

        # Primary suggestion: truncate the prompt
        truncation_ratio = context_size / prompt_tokens if prompt_tokens > 0 else 1
        if truncation_ratio < 0.8:
            suggestions.append(
                f"Truncate the prompt to fit within the model's {context_size} token context limit. "
                f"Your prompt is estimated at {prompt_tokens} tokens, which is {prompt_tokens - context_size} tokens over the limit."
            )
        else:
            suggestions.append(
                f"Consider truncating the prompt to better utilize the available {context_size} token context."
            )

        # Secondary suggestion: use a different model
        available_models = self.available_models
        larger_models = [m for m in available_models if self.get_context_size(m) > context_size]

        if larger_models:
            largest_model = max(larger_models, key=lambda m: self.get_context_size(m))
            largest_context = self.get_context_size(largest_model)
            suggestions.append(
                f"Switch to a model with larger context window. '{largest_model}' has {largest_context} tokens "
                f"({largest_context - context_size} more than '{model}')."
            )

        # Tertiary suggestion: break into chunks
        if prompt_tokens > context_size * 2:
            chunk_count = (prompt_tokens // context_size) + 1
            suggestions.append(
                f"Break the request into {chunk_count} smaller chunks to process separately."
            )

        # Quaternary suggestion: optimize token usage
        suggestions.append(
            "Consider removing redundant information, using more concise language, or "
            "focusing on the most essential parts of your query."
        )

        return " ".join(suggestions[:2])  # Return top 2 suggestions

    def check_context_fit(self, prompt: str, model: str) -> tuple[bool, str | None]:
        """Check if a prompt will fit within the model's context size.

        Args:
            prompt: The prompt to check
            model: The model identifier

        Returns:
            Tuple of (will_fit, warning_message)
        """
        estimated_tokens = self.estimate_prompt_tokens(prompt)
        context_size = self.get_context_size(model)
        reserved_for_response = min(512, context_size // 4)
        available_for_prompt = context_size - reserved_for_response

        if estimated_tokens <= available_for_prompt:
            return True, None

        return False, (
            f"Prompt estimated at {estimated_tokens} tokens exceeds available context "
            f"({available_for_prompt} tokens) for model {model}. Consider truncating or "
            "using a model with larger context window."
        )

    def get_adaptive_token_budget(self, model: str, base_budget: int | None = None) -> int:
        """Get adaptive token budget based on model capabilities and usage history.

        Args:
            model: The model identifier
            base_budget: Optional base budget to start from

        Returns:
            Adaptive token budget that considers model capabilities and performance
        """
        if base_budget is None:
            base_budget = self.get_context_size(model)

        # Adjust budget based on model capabilities
        context_size = self.get_context_size(model)

        # Use adaptive scaling based on model size and performance history
        adaptive_factor = self._calculate_adaptive_factor(model)

        # Apply adaptive factor but stay within safe bounds
        adaptive_budget = int(base_budget * adaptive_factor)
        adaptive_budget = max(1024, min(adaptive_budget, context_size - 512))

        return adaptive_budget

    def _calculate_adaptive_factor(self, model: str) -> float:
        """Calculate adaptive factor based on model capabilities and usage patterns.

        Args:
            model: The model identifier

        Returns:
            Adaptive factor (0.5-1.2 range typically)
        """
        base_factor = 0.8  # Conservative base factor

        # Adjust based on model size (larger models can handle more tokens)
        context_size = self.get_context_size(model)
        if context_size >= 16384:
            base_factor *= 1.2  # Large context models
        elif context_size >= 8192:
            base_factor *= 1.1  # Medium context models
        elif context_size <= 4096:
            base_factor *= 0.9  # Small context models

        # Adjust based on usage history (if available)
        if model in self._token_usage_history and self._token_usage_history[model]:
            # If we've successfully used high token counts before, be more aggressive
            recent_usage = self._token_usage_history[model][-5:]  # Last 5 uses
            avg_usage = sum(recent_usage) / len(recent_usage)

            if avg_usage > context_size * 0.8:  # Using >80% of context successfully
                base_factor *= 1.1
            elif avg_usage < context_size * 0.5:  # Using <50% of context
                base_factor *= 0.9

        # Adjust based on performance metrics (if available)
        if model in self._performance_metrics:
            metrics = self._performance_metrics[model]

            # If model performs well with higher token counts, increase factor
            if metrics.get("success_rate", 0) > 0.9 and metrics.get("avg_tokens", 0) > context_size * 0.7:
                base_factor *= 1.05

        # Keep factor within reasonable bounds
        return max(0.6, min(base_factor, 1.3))

    def record_token_usage(self, model: str, prompt_tokens: int, response_tokens: int, success: bool = True) -> None:
        """Record token usage for adaptive budgeting.

        Args:
            model: The model identifier
            prompt_tokens: Number of tokens used in prompt
            response_tokens: Number of tokens generated in response
            success: Whether the request was successful
        """
        if model not in self._token_usage_history:
            self._token_usage_history[model] = []

        # Keep only recent history (last 20 requests)
        self._token_usage_history[model].append(prompt_tokens + response_tokens)
        if len(self._token_usage_history[model]) > 20:
            self._token_usage_history[model] = self._token_usage_history[model][-20:]

        # Update performance metrics
        if model not in self._performance_metrics:
            self._performance_metrics[model] = {"success_count": 0, "total_count": 0, "total_tokens": 0}

        self._performance_metrics[model]["total_count"] += 1
        self._performance_metrics[model]["total_tokens"] += prompt_tokens + response_tokens

        if success:
            self._performance_metrics[model]["success_count"] += 1

        # Calculate derived metrics
        success_rate = self._performance_metrics[model]["success_count"] / self._performance_metrics[model]["total_count"]
        avg_tokens = self._performance_metrics[model]["total_tokens"] / self._performance_metrics[model]["total_count"]

        self._performance_metrics[model]["success_rate"] = success_rate
        self._performance_metrics[model]["avg_tokens"] = avg_tokens

    def get_model_performance_report(self, model: str | None = None) -> dict[str, Any]:
        """Get performance report for models.

        Args:
            model: Optional specific model to report on, or None for all models

        Returns:
            Performance report dictionary
        """
        if model:
            if model in self._performance_metrics:
                return {
                    "model": model,
                    "metrics": self._performance_metrics[model],
                    "context_size": self.get_context_size(model),
                    "recent_usage": self._token_usage_history.get(model, []),
                }
            else:
                return {"model": model, "error": "No performance data available"}
        else:
            return {
                "models": list(self._performance_metrics.keys()),
                "context_sizes": {m: self.get_context_size(m) for m in self._performance_metrics.keys()},
                "performance_metrics": self._performance_metrics,
                "usage_history": self._token_usage_history,
            }

    def validate_model(self, model: str | None) -> str:
        """Return the provided model without restricting LM Studio identifiers.

        For LM Studio, we allow any model identifier since LM Studio supports
        various model formats and the API will validate the actual model.
        """
        if model:
            return model
        return super().validate_model(model)

    def get_model_info(self) -> dict[str, Any]:
        """Get information about model discovery status and context size awareness.

        Returns:
            Dictionary containing discovery status, available models, and context size information
        """
        # Determine if we're using actually discovered models vs fallbacks
        using_actual_discovery = (
            bool(self._discovered_models) and
            not self._model_discovery_error and
            self._discovered_models != self._fallback_models
        )

        return {
            "discovered_models": self._discovered_models,
            "fallback_models": self._fallback_models,
            "discovery_error": self._model_discovery_error,
            "endpoint": self.endpoint,
            "using_discovered": using_actual_discovery,
            "model_context_sizes": self._model_context_sizes,
            "context_warnings": self._context_warnings,
            "performance_metrics": self._performance_metrics,
            "token_usage_history": self._token_usage_history,
        }

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        """Generate text using the LM Studio local API with context size awareness.

        Args:
            prompt: The prompt to generate text from
            model: Optional model name to use, defaults to the first available model
            **kwargs: Additional arguments to pass to the API

        Returns:
            The generated text response

        Raises:
            LLMError: If there's an error communicating with the LM Studio API or context size issues
        """
        model = self.validate_model(model)

        # Check if prompt fits within context size
        fits, warning = self.check_context_fit(prompt, model)
        if not fits and warning:
            # Try to truncate the prompt
            truncated_prompt = self.truncate_prompt(prompt, model)
            if truncated_prompt != prompt:
                # Use truncated prompt but log the warning
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Prompt truncated for model {model}: {warning}")

        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }

        # Add max_tokens if specified in kwargs or if we need to limit context
        if "max_tokens" not in kwargs:
            # Use adaptive token budgeting based on model capabilities and usage history
            adaptive_budget = self.get_adaptive_token_budget(model)
            payload["max_tokens"] = adaptive_budget

        session: RequestsSessionProtocol = get_session()
        try:
            resp: RequestsResponseProtocol = session.post(
                self.endpoint, json=payload, timeout=self.timeout
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            from ..errors import LLMError

            detail: Dict[str, Any] = {
                "status_code": exc.response.status_code if exc.response is not None else None,
                "response_text": (
                    exc.response.text[:500] if exc.response is not None and hasattr(exc.response, 'text') and exc.response.text else ""
                ),
                "payload_keys": list(payload.keys()),
                "context_size": self.get_context_size(model),
                "estimated_prompt_tokens": self.estimate_prompt_tokens(prompt),
            }

            # Check if this is a context size error and provide intelligent recovery suggestions
            response_text = detail["response_text"]
            context_size = detail.get("context_size", self.get_context_size(model))
            prompt_tokens = detail.get("estimated_prompt_tokens", 0)

            if any(keyword in response_text.lower() for keyword in ["context", "token", "length", "size", "exceed", "maximum", "limit"]):
                # This is likely a context size error - provide intelligent recovery suggestions
                suggestion = self._generate_context_size_suggestion(model, context_size, prompt_tokens)
            elif "rate limit" in response_text.lower() or "too many requests" in response_text.lower():
                suggestion = (
                    "Rate limit exceeded. Please wait a moment before retrying, "
                    "or consider using a different model with higher rate limits."
                )
            elif "model" in response_text.lower() and ("not found" in response_text.lower() or "unavailable" in response_text.lower()):
                suggestion = (
                    f"Model '{model}' is not available or not loaded in LM Studio. "
                    "Please ensure the model is properly loaded in LM Studio, or select a different model."
                )
            else:
                suggestion = (
                    "Inspect LM Studio server logs for request validation errors "
                    "and verify the selected model supports the prompt size."
                )

            # Record failed usage for adaptive budgeting
            prompt_tokens = self.estimate_prompt_tokens(prompt)
            self.record_token_usage(model, prompt_tokens, 0, success=False)

            raise LLMError(
                "Failed to generate response from LM Studio",
                cause=exc,
                model=model,
                suggestion=suggestion,
                metadata=detail,
            ) from exc
        except requests.RequestException as exc:
            from ..errors import LLMError

            # Record failed usage for adaptive budgeting
            prompt_tokens = self.estimate_prompt_tokens(prompt)
            self.record_token_usage(model, prompt_tokens, 0, success=False)

            raise LLMError(
                "Failed to generate response from LM Studio",
                cause=exc,
                model=model,
                suggestion="Ensure LM Studio is running and accessible at the configured endpoint",
            ) from exc

        data: Dict[str, Any] = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        generated_text = str(content) if content is not None else ""

        # Record successful usage for adaptive budgeting
        prompt_tokens = self.estimate_prompt_tokens(prompt)
        response_tokens = self.estimate_prompt_tokens(generated_text)
        self.record_token_usage(model, prompt_tokens, response_tokens, success=True)

        return generated_text

    def _get_intelligent_fallback(self, config, agent_name: str) -> str:
        """Get intelligent fallback model based on available models and context."""
        # If using LM Studio, try to get a model from discovery
        if config is not None and hasattr(config, 'llm_backend') and config.llm_backend == "lmstudio":
            try:
                model_info = self.get_model_info()

                if model_info.get("using_discovered", False) and model_info.get("discovered_models"):
                    discovered_models = model_info["discovered_models"]

                    # Prefer models with larger context sizes
                    best_model = None
                    best_context_size = 0

                    for model in discovered_models[:3]:  # Check first 3 models
                        try:
                            context_size = self.get_context_size(model)
                            if context_size > best_context_size:
                                best_context_size = context_size
                                best_model = model
                        except Exception:
                            continue

                    if best_model:
                        return best_model

            except Exception as e:
                logger.debug(f"Intelligent fallback discovery failed: {e}")

        # Fallback to conservative defaults based on backend
        if config is not None and hasattr(config, 'llm_backend'):
            if config.llm_backend == "lmstudio":
                return "mistral"  # Conservative LM Studio default
            elif config.llm_backend == "openai":
                return "gpt-3.5-turbo"  # Conservative OpenAI default
            elif config.llm_backend == "openrouter":
                return "anthropic/claude-3-haiku"  # Conservative OpenRouter default

        return "mistral"  # Global conservative default


class OpenAIAdapter(LLMAdapter):
    """Adapter for the OpenAI API with context awareness and accurate token counting."""

    # Known context sizes for OpenAI models (fallback if API unavailable)
    _model_context_sizes = {
        "gpt-3.5-turbo": 16385,
        "gpt-3.5-turbo-16k": 16385,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-4-turbo-preview": 128000,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
    }

    @property
    def available_models(self) -> list[str]:
        """Return available models for the OpenAI adapter."""
        return list(self._model_context_sizes.keys())

    def __init__(self) -> None:
        """Initialize the OpenAI adapter with context awareness.

        The API key is read from the OPENAI_API_KEY environment variable.
        The endpoint can be customized using the OPENAI_ENDPOINT environment variable.
        """
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.endpoint = os.getenv(
            "OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions"
        )

        # Cache for model context sizes
        self._context_cache: dict[str, int] = {}
        self._context_cache_ttl: dict[str, float] = {}

    def get_context_size(self, model: str) -> int:
        """Get context size for OpenAI model.

        Args:
            model: The model identifier

        Returns:
            Context size in tokens
        """
        # Check cache first (5 minute TTL)
        import time
        current_time = time.time()
        if model in self._context_cache:
            cache_time = self._context_cache_ttl.get(model, 0)
            if current_time - cache_time < 300:  # 5 minutes
                return self._context_cache[model]

        # Try exact match first
        if model in self._model_context_sizes:
            context_size = self._model_context_sizes[model]
        else:
            # Try prefix match for model variants
            context_size = None
            for known_model, size in self._model_context_sizes.items():
                if model.startswith(known_model):
                    context_size = size
                    break

            if context_size is None:
                # Default conservative estimate
                context_size = 4096

        # Cache the result
        self._context_cache[model] = context_size
        self._context_cache_ttl[model] = current_time

        return context_size

    def estimate_prompt_tokens(self, prompt: str) -> int:
        """Estimate tokens in prompt using tiktoken for OpenAI models.

        Args:
            prompt: The prompt text to estimate tokens for

        Returns:
            Estimated token count using tiktoken when available
        """
        from .token_counting import count_tokens_accurate
        return count_tokens_accurate(prompt, self.validate_model(None), "openai")

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
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
                suggestion="Set the OPENAI_API_KEY environment variable with your API key",
            )

        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}
            session: RequestsSessionProtocol = get_session()
            response: RequestsResponseProtocol = session.post(
                self.endpoint, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return str(content) if content is not None else ""
        except requests.RequestException as e:
            from ..errors import LLMError

            raise LLMError(
                "Failed to generate response from OpenAI API",
                cause=e,
                model=model,
                suggestion="Check your API key and internet connection, or try a different model",
            )


class OpenRouterAdapter(LLMAdapter):
    """Adapter for the OpenRouter.ai API with dynamic context detection."""

    # Default context sizes for OpenRouter models (fallback)
    _default_model_contexts = {
        "anthropic/claude-3-opus": 200000,
        "anthropic/claude-3-sonnet": 200000,
        "anthropic/claude-3-haiku": 200000,
        "mistralai/mistral-large": 32768,
        "mistralai/mistral-medium": 32768,
        "mistralai/mistral-small": 32768,
        "google/gemini-pro": 32768,
        "google/gemini-1.5-pro": 2097152,
        "google/gemini-flash-1.5": 1048576,  # Free tier model
        "meta-llama/llama-3-70b-instruct": 8192,
        "meta-llama/llama-3-8b-instruct": 8192,
        "meta-llama/llama-3.2-3b-instruct": 131072,  # Free tier model
        "qwen/qwen-2-7b-instruct": 32768,  # Free tier model
        "nousresearch/hermes-3-llama-3.1-405b": 131072,  # Free tier model
    }

    def __init__(self) -> None:
        """Initialize the OpenRouter adapter with context awareness and adaptive budgeting.

        The API key is read from the OPENROUTER_API_KEY environment variable.
        The endpoint can be customized using the OPENROUTER_ENDPOINT environment variable.
        The cache TTL can be customized using the OPENROUTER_CACHE_TTL environment variable.
        The timeout can be customized using the OPENROUTER_TIMEOUT environment variable.
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.endpoint = os.getenv(
            "OPENROUTER_ENDPOINT", "https://openrouter.ai/api/v1/chat/completions"
        )

        # Cache for model context sizes from API
        self._model_context_sizes: dict[str, int] = {}
        self._context_cache_ttl: dict[str, float] = {}

        # Configurable cache TTL (default: 1 hour)
        self._cache_ttl = int(os.getenv("OPENROUTER_CACHE_TTL", "3600"))  # seconds

        # Configurable timeout (default: 60 seconds)
        timeout_env = os.getenv("OPENROUTER_TIMEOUT")
        try:
            self.timeout = float(timeout_env) if timeout_env else 60.0
        except (TypeError, ValueError):  # pragma: no cover - defensive
            self.timeout = 60.0

        # Performance tracking for adaptive budgeting (similar to LMStudioAdapter)
        self._token_usage_history: dict[str, list[int]] = {}  # Track token usage per model
        self._performance_metrics: dict[str, dict[str, float]] = {}  # Track performance metrics
        self._context_warnings: dict[str, str] = {}

        # Discover models on initialization
        self._discover_models()

    @property
    def available_models(self) -> list[str]:
        """Return available models for the OpenRouter adapter."""
        return list(self._default_model_contexts.keys())

    def _discover_models(self) -> None:
        """Discover models and context sizes from OpenRouter API."""
        if not self.api_key:
            logger.debug("OpenRouter API key not set, using default context sizes")
            self._model_context_sizes = self._default_model_contexts.copy()
            return

        try:
            # Query the OpenRouter models endpoint
            url = "https://openrouter.ai/api/v1/models"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/ravenoak/autoresearch",
                "X-Title": "Autoresearch",
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Process the models data
            for model in data.get("data", []):
                model_id = model.get("id")
                context_length = model.get("context_length")

                if model_id and context_length:
                    self._model_context_sizes[model_id] = context_length
                    logger.debug(f"OpenRouter model {model_id}: context_length={context_length}")

        except Exception as e:
            logger.error(f"Error discovering OpenRouter models: {e}")
            logger.debug("Using default context sizes for OpenRouter models")
            self._model_context_sizes = self._default_model_contexts.copy()

    def get_context_size(self, model: str) -> int:
        """Get context size for OpenRouter model.

        Args:
            model: The model identifier

        Returns:
            Context size in tokens
        """
        # Check cache first (configurable TTL)
        import time
        current_time = time.time()
        if model in self._model_context_sizes:
            cache_time = self._context_cache_ttl.get(model, 0)
            if current_time - cache_time < self._cache_ttl:
                return self._model_context_sizes[model]

        # Get from API or defaults
        if model in self._model_context_sizes:
            context_size = self._model_context_sizes[model]
        else:
            # Try to discover this specific model
            self._discover_models()
            context_size = self._model_context_sizes.get(model, 4096)  # Conservative fallback

        # Cache the result
        self._model_context_sizes[model] = context_size
        self._context_cache_ttl[model] = current_time

        return context_size

    def refresh_model_cache(self) -> None:
        """Manually refresh the model discovery cache.

        This forces a fresh discovery of models from the OpenRouter API,
        bypassing the cache. Useful for getting updated model information.
        """
        logger.debug("Manually refreshing OpenRouter model cache")
        self._model_context_sizes.clear()
        self._context_cache_ttl.clear()
        self._discover_models()

    def clear_model_cache(self) -> None:
        """Clear the model discovery cache.

        This removes all cached model information, forcing fresh discovery
        on the next context size request.
        """
        logger.debug("Clearing OpenRouter model cache")
        self._model_context_sizes.clear()
        self._context_cache_ttl.clear()

    def check_context_fit(self, prompt: str, model: str) -> tuple[bool, str | None]:
        """Check if a prompt will fit within the model's context size.

        Args:
            prompt: The prompt to check
            model: The model identifier

        Returns:
            Tuple of (will_fit, warning_message)
        """
        estimated_tokens = self.estimate_prompt_tokens(prompt)
        context_size = self.get_context_size(model)
        reserved_for_response = min(512, context_size // 4)
        available_for_prompt = context_size - reserved_for_response

        if estimated_tokens <= available_for_prompt:
            return True, None

        # Calculate how much we exceed by
        excess_tokens = estimated_tokens - available_for_prompt
        warning = (
            f"Prompt exceeds context limit by {excess_tokens} tokens. "
            f"Context size: {context_size}, available: {available_for_prompt}, "
            f"estimated: {estimated_tokens} tokens."
        )
        return False, warning

    def truncate_prompt(self, prompt: str, model: str, max_tokens: int | None = None) -> str:
        """Truncate a prompt to fit within context size limits using intelligent truncation.

        Args:
            prompt: The prompt to truncate
            model: The model identifier to get context size for
            max_tokens: Optional maximum tokens to allow (overrides model context)

        Returns:
            Truncated prompt that should fit within context limits
        """
        if max_tokens is None:
            max_tokens = self.get_context_size(model)

        # Reserve tokens for response generation (rough estimate)
        reserved_for_response = min(512, max_tokens // 4)
        available_for_prompt = max_tokens - reserved_for_response

        estimated_tokens = self.estimate_prompt_tokens(prompt)

        if estimated_tokens <= available_for_prompt:
            return prompt

        # Use intelligent truncation that preserves important content
        return self._intelligently_truncate_prompt(prompt, available_for_prompt)

    def _intelligently_truncate_prompt(self, prompt: str, max_tokens: int) -> str:
        """Intelligently truncate a prompt to preserve the most important content.

        Args:
            prompt: The prompt to truncate
            max_tokens: Maximum tokens to allow

        Returns:
            Intelligently truncated prompt
        """
        # Use conservative character estimate (3 chars per token)
        max_chars = max_tokens * 3

        if len(prompt) <= max_chars:
            return prompt

        # Simple truncation for now - could be enhanced with NLP-based importance scoring
        truncated = prompt[:max_chars]

        # Try to end at a sentence boundary if possible
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')

        if last_period > max_chars * 0.8:  # If period is in last 20% of allowed chars
            return truncated[:last_period + 1]
        elif last_newline > max_chars * 0.8:  # If newline is in last 20% of allowed chars
            return truncated[:last_newline]

        return truncated

    def get_adaptive_token_budget(self, model: str, base_budget: int | None = None) -> int:
        """Get adaptive token budget based on model capabilities and usage history.

        Args:
            model: The model identifier
            base_budget: Optional base budget to start from

        Returns:
            Adaptive token budget that considers model capabilities and performance
        """
        if base_budget is None:
            base_budget = self.get_context_size(model)

        # Adjust budget based on model capabilities
        context_size = self.get_context_size(model)

        # Use adaptive scaling based on model size and performance history
        adaptive_factor = self._calculate_adaptive_factor(model)

        # Apply adaptive factor but stay within safe bounds
        adaptive_budget = int(base_budget * adaptive_factor)

        # Ensure we don't exceed context size
        return min(adaptive_budget, context_size)

    def _calculate_adaptive_factor(self, model: str) -> float:
        """Calculate adaptive factor based on model performance and usage patterns.

        Args:
            model: The model identifier

        Returns:
            Adaptive factor (0.5 to 1.0) to scale token budget
        """
        # Base factor
        base_factor = 0.8

        # Adjust based on model size (larger models can handle more tokens)
        context_size = self.get_context_size(model)
        if context_size > 100000:
            base_factor *= 0.9  # Very large models
        elif context_size > 50000:
            base_factor *= 0.85  # Large models
        elif context_size > 10000:
            base_factor *= 0.8   # Medium models
        else:
            base_factor *= 0.7   # Small models

        # Adjust based on usage history (if we have data)
        if model in self._token_usage_history:
            usage_history = self._token_usage_history[model]
            if len(usage_history) >= 5:
                # If we've had successful generations, be more aggressive
                recent_usage = usage_history[-5:]
                success_rate = sum(1 for tokens in recent_usage if tokens > 0) / len(recent_usage)
                if success_rate > 0.8:
                    base_factor *= 1.1  # Increase budget for reliable models

        # Ensure factor stays within reasonable bounds
        return max(0.5, min(1.0, base_factor))

    def record_token_usage(self, model: str, prompt_tokens: int, response_tokens: int, success: bool = True) -> None:
        """Record token usage for adaptive budgeting.

        Args:
            model: The model identifier
            prompt_tokens: Number of tokens in the prompt
            response_tokens: Number of tokens in the response
            success: Whether the generation was successful
        """
        if model not in self._token_usage_history:
            self._token_usage_history[model] = []

        # Keep only recent history (last 20 usages)
        self._token_usage_history[model].append(prompt_tokens + response_tokens)
        self._token_usage_history[model] = self._token_usage_history[model][-20:]

    def estimate_prompt_tokens(self, prompt: str) -> int:
        """Estimate tokens in prompt using appropriate tokenizer.

        Args:
            prompt: The prompt text to estimate tokens for

        Returns:
            Estimated token count using best available method
        """
        from .token_counting import count_tokens_accurate

        # Determine provider based on model prefix
        provider = "openrouter"
        if model := self.validate_model(None):
            if model.startswith(("anthropic/", "claude")):
                provider = "anthropic"
            elif model.startswith(("google/", "gemini")):
                provider = "google"
            elif model.startswith(("mistralai/", "mistral")):
                provider = "mistral"
            elif model.startswith(("meta-llama/", "llama")):
                provider = "meta"

        return count_tokens_accurate(prompt, model, provider)

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        """Generate text using the OpenRouter.ai API with context size awareness.

        Args:
            prompt: The prompt to generate text from
            model: Optional model name to use, defaults to the first available model
            **kwargs: Additional arguments to pass to the API

        Returns:
            The generated text response

        Raises:
            LLMError: If the API key is missing or there's an error communicating with the OpenRouter API or context size issues
        """
        model = self.validate_model(model)

        if not self.api_key:
            from ..errors import LLMError

            raise LLMError(
                "OpenRouter API key not found",
                model=model,
                suggestion="Set the OPENROUTER_API_KEY environment variable with your API key",
            )

        # Check if prompt fits within context size (similar to LMStudioAdapter)
        fits, warning = self.check_context_fit(prompt, model)
        if not fits and warning:
            # Try to truncate the prompt
            truncated_prompt = self.truncate_prompt(prompt, model)
            if truncated_prompt != prompt:
                # Use truncated prompt but log the warning
                logger.warning(f"Prompt truncated for model {model}: {warning}")
                prompt = truncated_prompt

        return self._generate_with_retries(prompt, model, **kwargs)

    def _generate_with_retries(self, prompt: str, model: str, **kwargs: Any) -> str:
        """Generate text with retry logic for rate limits and server errors.

        Args:
            prompt: The prompt to generate text from
            model: Model name to use
            **kwargs: Additional arguments to pass to the API

        Returns:
            The generated text response

        Raises:
            LLMError: If all retry attempts fail
        """
        max_retries = 3
        base_delay = 1.0  # Start with 1 second
        max_delay = 60.0  # Maximum 60 seconds

        last_exception = None

        for attempt in range(max_retries):
            try:
                return self._make_api_call(prompt, model, **kwargs)

            except requests.RequestException as e:
                last_exception = e

                # Record failed usage for adaptive budgeting
                prompt_tokens = self.estimate_prompt_tokens(prompt)
                self.record_token_usage(model, prompt_tokens, 0, success=False)

                # Check if this is a retryable error
                if not self._is_retryable_error(e):
                    logger.debug(f"Non-retryable error on attempt {attempt + 1}: {e}")
                    break

                # Don't retry on the last attempt
                if attempt == max_retries - 1:
                    logger.debug(f"Max retries ({max_retries}) exceeded")
                    break

                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                # Check for Retry-After header
                retry_after = self._get_retry_after_header(e)
                if retry_after:
                    delay = max(delay, retry_after)

                logger.warning(f"OpenRouter API error on attempt {attempt + 1}/{max_retries}: {e}. Retrying in {delay}s...")
                time.sleep(delay)

        # All retries failed, raise the last exception
        from ..errors import LLMError

        raise LLMError(
            f"Failed to generate response from OpenRouter API after {max_retries} attempts",
            cause=last_exception,
            model=model,
            suggestion="Check your API key, rate limits, and internet connection",
        )

    def _make_api_call(self, prompt: str, model: str, **kwargs: Any) -> str:
        """Make a single API call to OpenRouter.

        Args:
            prompt: The prompt to generate text from
            model: Model name to use
            **kwargs: Additional arguments to pass to the API

        Returns:
            The generated text response

        Raises:
            requests.RequestException: If the API call fails
        """
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }

        # Add max_tokens if specified in kwargs or if we need to limit context (similar to LMStudioAdapter)
        if "max_tokens" not in kwargs:
            # Use adaptive token budgeting based on model capabilities and usage history
            adaptive_budget = self.get_adaptive_token_budget(model)
            payload["max_tokens"] = adaptive_budget

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/ravenoak/autoresearch",
            "X-Title": "Autoresearch",
        }
        session: RequestsSessionProtocol = get_session()
        response: RequestsResponseProtocol = session.post(
            self.endpoint, json=payload, headers=headers, timeout=self.timeout
        )

        # Enhanced error handling for OpenRouter-specific errors
        if not response.ok:
            self._handle_openrouter_error(response, model)

        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        response_text = str(content) if content is not None else ""

        # Record successful usage for adaptive budgeting
        prompt_tokens = self.estimate_prompt_tokens(prompt)
        response_tokens = self.estimate_prompt_tokens(response_text)
        self.record_token_usage(model, prompt_tokens, response_tokens, success=True)

        return response_text

    def _handle_openrouter_error(self, response: RequestsResponseProtocol, model: str) -> None:
        """Handle OpenRouter-specific HTTP errors with intelligent recovery suggestions.

        Args:
            response: The HTTP response object
            model: The model that was requested

        Raises:
            requests.HTTPError: With enhanced error message for OpenRouter-specific errors
        """
        status_code = response.status_code

        # Try to get error details from response body
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
        except (ValueError, AttributeError):
            error_message = f"HTTP {status_code}"

        # Enhanced error analysis similar to LMStudioAdapter
        detail = {
            "status_code": status_code,
            "response_text": error_message,
            "context_size": self.get_context_size(model),
        }

        # Check if this is a context size error and provide intelligent recovery suggestions
        response_text = detail["response_text"]
        context_size = detail.get("context_size", self.get_context_size(model))

        if any(keyword in response_text.lower() for keyword in ["context", "token", "length", "size", "exceed", "maximum", "limit"]):
            # This is likely a context size error - provide intelligent recovery suggestions
            suggestion = self._generate_context_size_suggestion(model, context_size, 0)
        elif "rate limit" in response_text.lower() or "too many requests" in response_text.lower():
            suggestion = (
                "Rate limit exceeded. Please wait a moment before retrying, "
                "or consider using a different model with higher rate limits."
            )
        elif "model" in response_text.lower() and ("not found" in response_text.lower() or "unavailable" in response_text.lower()):
            suggestion = (
                f"Model '{model}' is not available or not loaded in OpenRouter. "
                "Please ensure the model is properly configured, or select a different model."
            )
        else:
            # Use standard error handling for other cases
            suggestion = self._get_standard_error_suggestion(status_code, model, error_message)

        # Create a new HTTPError with enhanced message
        from requests import HTTPError
        http_error = HTTPError(f"{error_message}. {suggestion}", response=response)
        raise http_error

    def _generate_context_size_suggestion(self, model: str, context_size: int, prompt_tokens: int) -> str:
        """Generate intelligent suggestions for context size errors.

        Args:
            model: The model identifier
            context_size: The model's context size
            prompt_tokens: Estimated tokens in the prompt

        Returns:
            Helpful suggestion for resolving context size issues
        """
        if prompt_tokens > context_size:
            excess = prompt_tokens - context_size
            return (
                f"Prompt exceeds context limit by {excess} tokens. "
                f"Context size: {context_size}, prompt: {prompt_tokens} tokens. "
                "Consider truncating your prompt or using a model with larger context."
            )
        else:
            return (
                "Context size error detected. "
                "Try using a model with larger context window or reducing prompt size."
            )

    def _get_standard_error_suggestion(self, status_code: int, model: str, error_message: str) -> str:
        """Get standard error suggestions for common error codes.

        Args:
            status_code: HTTP status code
            model: The model identifier
            error_message: The error message from the API

        Returns:
            Appropriate suggestion for the error
        """
        if status_code == 400:
            # Bad request - often invalid model
            return f"Check if model '{model}' is valid and supported by OpenRouter"
        elif status_code == 401:
            # Unauthorized - invalid API key
            return "Check your OPENROUTER_API_KEY environment variable"
        elif status_code == 402:
            # Payment required - insufficient credits
            return "Add credits to your OpenRouter account or use free-tier models"
        elif status_code == 403:
            # Forbidden - API key doesn't have access to model
            return "Check if your API key has access to this model or try a different model"
        elif status_code == 404:
            # Not found - model doesn't exist
            return "Check if the model name is correct or try a different model"
        elif status_code == 429:
            # Rate limit exceeded
            return "Wait before retrying or check your rate limits"
        elif 500 <= status_code < 600:
            # Server errors
            return "This is likely a temporary issue, try again later"
        else:
            # Generic error
            return "Check OpenRouter status page or contact support"

    def _is_retryable_error(self, exception: requests.RequestException) -> bool:
        """Check if an error is retryable.

        Args:
            exception: The exception to check

        Returns:
            True if the error should be retried
        """
        if isinstance(exception, requests.HTTPError):
            response = exception.response
            if response:
                status_code = response.status_code
                # Retry on rate limits (429), server errors (5xx), and some client errors (4xx)
                return status_code == 429 or (500 <= status_code < 600) or status_code in (408, 502, 503, 504)

        # Retry on connection errors, timeouts, etc.
        return isinstance(exception, (
            requests.ConnectionError,
            requests.Timeout,
            requests.ConnectTimeout,
            requests.ReadTimeout,
        ))

    def _get_retry_after_header(self, exception: requests.RequestException) -> float | None:
        """Get retry delay from Retry-After header if present.

        Args:
            exception: The exception to check

        Returns:
            Delay in seconds, or None if not available
        """
        if isinstance(exception, requests.HTTPError) and exception.response:
            retry_after = exception.response.headers.get("Retry-After")
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass
        return None

    def generate_stream(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        """Generate text using the OpenRouter.ai API with streaming support.

        Args:
            prompt: The prompt to generate text from
            model: Optional model name to use, defaults to the first available model
            **kwargs: Additional arguments to pass to the API

        Returns:
            The generated text response (streaming not fully implemented yet)

        Raises:
            LLMError: If the API key is missing or there's an error communicating with the OpenRouter API
        """
        model = self.validate_model(model)

        if not self.api_key:
            from ..errors import LLMError

            raise LLMError(
                "OpenRouter API key not found",
                model=model,
                suggestion="Set the OPENROUTER_API_KEY environment variable with your API key",
            )

        # For now, fall back to non-streaming generation
        # TODO: Implement full streaming support with Server-Sent Events
        logger.warning("Streaming not fully implemented for OpenRouter, falling back to regular generation")
        return self._generate_with_retries(prompt, model, **kwargs)
