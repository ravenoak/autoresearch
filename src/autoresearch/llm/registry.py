"""Registry and factory for LLM adapters."""
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
                raise ValueError(f"Unknown LLM backend: {name}")
            return cls._registry[name]()


def get_llm_adapter(name: str) -> LLMAdapter:
    """Convenience wrapper to fetch adapter instance."""
    return LLMFactory.get(name)
