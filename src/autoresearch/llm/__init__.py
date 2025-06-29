"""Language Model (LLM) integration module for Autoresearch.

This module provides adapters for different LLM backends, a factory for creating
adapters, and utilities for token counting and management.
"""

from .registry import LLMFactory, get_llm_adapter, get_available_adapters
from .adapters import (
    LLMAdapter,
    DummyAdapter,
    LMStudioAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
)

# Register default backends
LLMFactory.register("dummy", DummyAdapter)
LLMFactory.register("lmstudio", LMStudioAdapter)
LLMFactory.register("openai", OpenAIAdapter)
LLMFactory.register("openrouter", OpenRouterAdapter)

__all__ = [
    "LLMAdapter",
    "LLMFactory",
    "get_llm_adapter",
    "get_available_adapters",
    "DummyAdapter",
    "LMStudioAdapter",
    "OpenAIAdapter",
    "OpenRouterAdapter",
]
