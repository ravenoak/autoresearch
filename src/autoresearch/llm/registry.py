"""Registry and factory for LLM adapters.

This module provides a factory pattern implementation for LLM adapters.
It includes:
- LLMFactory: A class that maintains a registry of adapter classes and creates instances
- get_llm_adapter: A convenience function to retrieve adapter instances

The registry uses thread-safe access to ensure concurrent safety.
"""

from __future__ import annotations

from typing import Dict, Type
from threading import Lock

from .adapters import LLMAdapter


class LLMFactory:
    """Factory to register and retrieve LLM adapters."""

    _registry: Dict[str, Type[LLMAdapter]] = {}
    _lock = Lock()

    @classmethod
    def register(cls, name: str, adapter_cls: Type[LLMAdapter]) -> None:
        with cls._lock:
            cls._registry[name] = adapter_cls

    @classmethod
    def get(cls, name: str) -> LLMAdapter:
        with cls._lock:
            if name not in cls._registry:
                from ..errors import LLMError

                available_backends = list(cls._registry.keys())
                raise LLMError(
                    f"Unknown LLM backend: {name}",
                    available_backends=available_backends,
                    provided=name,
                    suggestion=f"Configure a valid LLM backend in your configuration file. Available backends: {', '.join(available_backends)}",
                )
            return cls._registry[name]()


def get_llm_adapter(name: str) -> LLMAdapter:
    """Convenience wrapper to fetch adapter instance.

    Args:
        name: The name of the adapter to retrieve

    Returns:
        An instance of the requested LLM adapter

    Raises:
        LLMError: If the requested adapter is not registered
    """
    return LLMFactory.get(name)


def get_available_adapters() -> Dict[str, Type[LLMAdapter]]:
    """Return a copy of the registered adapter mapping."""
    with LLMFactory._lock:
        return dict(LLMFactory._registry)
