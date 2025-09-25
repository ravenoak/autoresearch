from __future__ import annotations

from typing import Any

from . import cli
from .language import Language


def load(model: str, *args: Any, **kwargs: Any) -> Language: ...


__all__ = ["Language", "cli", "load"]
