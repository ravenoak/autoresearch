"""Context size management utilities for LLM operations.

This module provides utilities for managing context sizes across different LLM providers,
including intelligent truncation, adaptive budgeting, and graceful error handling.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging

from ..errors import LLMError

logger = logging.getLogger(__name__)


class ContextOverflowStrategy(str, Enum):
    """Strategy for handling context overflow."""
    TRUNCATE = "truncate"
    CHUNK = "chunk"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of context validation."""
    fits: bool
    estimated_tokens: int
    available_tokens: int
    overflow_tokens: int
    should_chunk: bool
    should_truncate: bool
    recommendation: str


class ContextManager:
    """Manages context size constraints and provides intelligent adaptation strategies."""

    def __init__(self) -> None:
        """Initialize the context manager."""
        self._model_context_sizes: Dict[str, int] = {}
        self._provider_registry: Dict[str, str] = {}  # model -> provider
        self._usage_history: Dict[str, List[int]] = {}
        self._performance_metrics: Dict[str, Dict[str, float]] = {}

    def register_adapter(self, provider: str, models: Dict[str, int]) -> None:
        """Register an adapter with its models and context sizes."""
        for model, context_size in models.items():
            self._model_context_sizes[model] = context_size
            self._provider_registry[model] = provider

    def register_model_context_size(self, model: str, context_size: int) -> None:
        """Register the context size for a specific model.

        Args:
            model: The model identifier
            context_size: The context size in tokens
        """
        self._model_context_sizes[model] = context_size

    def get_context_size(self, model: str) -> int:
        """Get the context size for a model.

        Args:
            model: The model identifier

        Returns:
            The context size in tokens, or 4096 as a conservative default
        """
        return self._model_context_sizes.get(model, 4096)

    def get_provider(self, model: str) -> str:
        """Get the provider for a model."""
        return self._provider_registry.get(model, "unknown")

    def estimate_tokens(self, text: str, model: str) -> int:
        """Estimate tokens using provider-appropriate method."""
        from .token_counting import count_tokens_accurate
        provider = self.get_provider(model)
        return count_tokens_accurate(text, model, provider)

    def estimate_tokens_approximate(self, text: str) -> int:
        """Estimate the number of tokens in text using a conservative heuristic.

        Args:
            text: The text to estimate tokens for

        Returns:
            Estimated token count (conservative estimate)
        """
        # Conservative token estimation: ~4 characters per token for English text
        return len(text) // 4

    def check_fit(self, prompt: str, model: str, reserved_tokens: int = 512) -> Tuple[bool, Optional[str]]:
        """Check if a prompt will fit within the model's context size.

        Args:
            prompt: The prompt to check
            model: The model identifier
            reserved_tokens: Tokens to reserve for response generation

        Returns:
            Tuple of (will_fit, warning_message)
        """
        estimated_tokens = self.estimate_tokens_approximate(prompt)
        context_size = self.get_context_size(model)
        available_tokens = context_size - reserved_tokens

        if estimated_tokens <= available_tokens:
            return True, None

        return False, (
            f"Prompt estimated at {estimated_tokens} tokens exceeds available context "
            f"({available_tokens} tokens) for model {model}. "
            f"Model context size: {context_size} tokens."
        )

    def validate_prompt_fit(
        self,
        prompt: str,
        model: str,
        provider: str,
        reserved_tokens: int = 512
    ) -> ValidationResult:
        """Validate if prompt fits within model's context size.

        Args:
            prompt: The prompt to check
            model: The model identifier
            provider: The provider name
            reserved_tokens: Tokens to reserve for response generation

        Returns:
            ValidationResult with fit status and recommendations
        """
        estimated_tokens = self.estimate_tokens(prompt, model)
        context_size = self.get_context_size(model)
        available_tokens = context_size - reserved_tokens
        overflow_tokens = max(0, estimated_tokens - available_tokens)

        fits = estimated_tokens <= available_tokens
        should_chunk = overflow_tokens > available_tokens * 0.5  # >50% overflow
        should_truncate = not fits and not should_chunk

        if fits:
            recommendation = "Prompt fits within context"
        elif should_chunk:
            recommendation = f"Chunk into ~{(estimated_tokens // available_tokens) + 1} segments"
        else:
            recommendation = f"Truncate by ~{overflow_tokens} tokens"

        return ValidationResult(
            fits=fits,
            estimated_tokens=estimated_tokens,
            available_tokens=available_tokens,
            overflow_tokens=overflow_tokens,
            should_chunk=should_chunk,
            should_truncate=should_truncate,
            recommendation=recommendation
        )

    def suggest_recovery_strategies(self, model: str, context_size: int, prompt_tokens: int) -> List[str]:
        """Suggest recovery strategies for context size errors.

        Args:
            model: The model identifier
            context_size: The model's context size
            prompt_tokens: Tokens in the original prompt

        Returns:
            List of suggested recovery strategies
        """
        strategies = []

        # Strategy 1: Truncate the prompt
        if prompt_tokens > context_size:
            excess_tokens = prompt_tokens - context_size
            strategies.append(
                f"Truncate the prompt by approximately {excess_tokens} tokens to fit within the {context_size} token limit."
            )

        # Strategy 2: Use a model with larger context
        for registered_model, model_context in self._model_context_sizes.items():
            if model_context > context_size:
                strategies.append(
                    f"Switch to '{registered_model}' which has a larger context window of {model_context} tokens."
                )
                break

        # Strategy 3: Break into chunks
        if prompt_tokens > context_size * 1.5:
            chunk_count = (prompt_tokens // context_size) + 1
            strategies.append(
                f"Break the request into {chunk_count} smaller chunks for separate processing."
            )

        # Strategy 4: Optimize content
        strategies.append(
            "Remove redundant information, use more concise language, or focus on the most essential parts of your query."
        )

        return strategies

    def record_usage(self, model: str, prompt_tokens: int, response_tokens: int, success: bool = True) -> None:
        """Record token usage for performance tracking.

        Args:
            model: The model identifier
            prompt_tokens: Tokens used in prompt
            response_tokens: Tokens generated in response
            success: Whether the request was successful
        """
        if model not in self._usage_history:
            self._usage_history[model] = []

        total_tokens = prompt_tokens + response_tokens
        self._usage_history[model].append(total_tokens)

        # Keep only recent history (last 20 requests)
        if len(self._usage_history[model]) > 20:
            self._usage_history[model] = self._usage_history[model][-20:]

        # Update performance metrics
        if model not in self._performance_metrics:
            self._performance_metrics[model] = {"success_count": 0, "total_count": 0, "total_tokens": 0}

        self._performance_metrics[model]["total_count"] += 1
        self._performance_metrics[model]["total_tokens"] += total_tokens

        if success:
            self._performance_metrics[model]["success_count"] += 1

    def get_performance_report(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get performance report for models.

        Args:
            model: Optional specific model to report on

        Returns:
            Performance report dictionary
        """
        if model:
            if model in self._performance_metrics:
                metrics = self._performance_metrics[model]
                success_rate = metrics["success_count"] / metrics["total_count"] if metrics["total_count"] > 0 else 0
                avg_tokens = metrics["total_tokens"] / metrics["total_count"] if metrics["total_count"] > 0 else 0

                return {
                    "model": model,
                    "context_size": self.get_context_size(model),
                    "success_rate": success_rate,
                    "average_tokens": avg_tokens,
                    "total_requests": metrics["total_count"],
                    "recent_usage": self._usage_history.get(model, []),
                }
            else:
                return {"model": model, "error": "No performance data available"}
        else:
            return {
                "models": list(self._performance_metrics.keys()),
                "context_sizes": {m: self.get_context_size(m) for m in self._performance_metrics.keys()},
                "performance_metrics": self._performance_metrics,
                "usage_history": self._usage_history,
            }

    def get_safe_budget(self, model: str, provider: str, safety_margin: float = 0.15) -> int:
        """Get safe token budget leaving margin for response and overhead.

        Args:
            model: The model identifier
            provider: The provider name
            safety_margin: Safety margin as fraction of context size

        Returns:
            Safe token budget for prompts
        """
        context_size = self.get_context_size(model)
        # Reserve tokens: min 512 or 15% of context (whichever is larger)
        reserve = max(512, int(context_size * safety_margin))
        return context_size - reserve

    def truncate_intelligently(self, prompt: str, model: str, max_tokens: Optional[int] = None) -> str:
        """Intelligently truncate a prompt to fit within context limits.

        Args:
            prompt: The prompt to truncate
            model: The model identifier
            max_tokens: Optional maximum tokens (overrides model context)

        Returns:
            Intelligently truncated prompt
        """
        if max_tokens is None:
            context_size = self.get_context_size(model)
            reserved_tokens = min(512, context_size // 4)
            max_tokens = context_size - reserved_tokens

        estimated_tokens = self.estimate_tokens(prompt, model)
        if estimated_tokens <= max_tokens:
            return prompt

        return self._truncate_by_sentences(prompt, max_tokens, model)

    def _truncate_by_sentences(self, prompt: str, max_tokens: int, model: str) -> str:
        """Truncate prompt by preserving complete sentences.

        Args:
            prompt: The prompt to truncate
            max_tokens: Maximum tokens to allow
            model: The model identifier for token counting

        Returns:
            Truncated prompt preserving sentence boundaries
        """
        # Use conservative character estimate (3 chars per token)
        max_chars = max_tokens * 3

        if len(prompt) <= max_chars:
            return prompt

        # Split into sentences and try to preserve complete sentences
        sentences = re.split(r'[.!?]+', prompt)
        current_prompt = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add the sentence with its punctuation
            test_prompt = current_prompt + sentence + ". "

            if self.estimate_tokens(test_prompt, model) <= max_tokens:
                current_prompt = test_prompt
            else:
                # If adding this sentence would exceed the limit, stop here
                break

        if current_prompt:
            return current_prompt.rstrip() + "... [content truncated to fit context]"
        else:
            # Fallback to simple character truncation
            return prompt[:max_chars] + "... [prompt truncated to fit context]"

# Global context manager instance
_context_manager_instance: Optional[ContextManager] = None

def get_context_manager() -> ContextManager:
    """Get the singleton context manager instance."""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
        # Register provider-specific models and context sizes
        _register_provider_adapters(_context_manager_instance)
    return _context_manager_instance


def _register_provider_adapters(context_mgr: ContextManager) -> None:
    """Register all available LLM adapters with their models and context sizes."""
    try:
        from ..llm.registry import get_available_adapters

        adapters = get_available_adapters()
        for provider_name, adapter_cls in adapters.items():
            try:
                adapter = adapter_cls()
                models = adapter.available_models
                context_sizes = {}

                for model in models:
                    try:
                        if hasattr(adapter, 'get_context_size'):
                            context_size = adapter.get_context_size(model)
                            context_sizes[model] = context_size
                        else:
                            # Fallback for adapters without get_context_size
                            context_sizes[model] = 4096  # Conservative default
                    except Exception as e:
                        logger.debug(f"Could not get context size for {provider_name}/{model}: {e}")
                        context_sizes[model] = 4096  # Conservative default

                if context_sizes:
                    context_mgr.register_adapter(provider_name, context_sizes)
                    logger.debug(f"Registered {provider_name} adapter with {len(context_sizes)} models")

            except Exception as e:
                logger.debug(f"Could not initialize {provider_name} adapter for registration: {e}")

    except Exception as e:
        logger.debug(f"Could not register provider adapters: {e}")

