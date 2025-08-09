"""LLM adapter utilities for the API layer.

This stub module provides a minimal implementation required by
``tests/integration/test_api_additional.py``. It exposes a function
returning the list of available LLM adapters, which is currently empty
in the test environment.
"""

from typing import Any, Dict


def get_available_adapters() -> Dict[str, Any]:
    """Return available LLM adapters keyed by identifier."""
    return {}


__all__ = ["get_available_adapters"]
