"""Utilities for importing optional dependencies during tests."""

from __future__ import annotations

import importlib
from typing import Any

import pytest


def import_or_skip(
    module_name: str,
    *,
    attr: str | None = None,
    reason: str | None = None,
) -> Any:
    """Import a module or attribute, skipping the test when unavailable."""

    try:
        module = importlib.import_module(module_name)
    except ImportError:
        skip_reason = reason or f"{module_name} is required for this test."
        pytest.skip(skip_reason, allow_module_level=True)
    except Exception as exc:
        skip_reason = reason or f"{module_name} import failed: {exc}"
        pytest.skip(skip_reason, allow_module_level=True)

    if attr is None:
        return module

    if not hasattr(module, attr):
        skip_reason = reason or f"{module_name} is missing attribute {attr}."
        pytest.skip(skip_reason, allow_module_level=True)

    return getattr(module, attr)


__all__ = ["import_or_skip"]
