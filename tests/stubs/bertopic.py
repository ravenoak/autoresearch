"""Typed stub for the :mod:`bertopic` package."""

from __future__ import annotations

import importlib.util
from types import ModuleType
from typing import Protocol, cast

from ._registry import install_stub_module


class BERTopicModule(Protocol):
    __version__: str


class _BERTopicModule(ModuleType):
    __version__ = "0.0"
    __spec__ = importlib.util.spec_from_loader("bertopic", loader=None)

    def __init__(self) -> None:
        super().__init__("bertopic")


if importlib.util.find_spec("bertopic") is None:
    bertopic = cast(
        BERTopicModule, install_stub_module("bertopic", _BERTopicModule)
    )
else:  # pragma: no cover
    try:
        import bertopic as _bertopic  # pragma: no cover
        bertopic = cast(BERTopicModule, _bertopic)
    except ImportError:
        # BERTopic has import issues, use stub instead
        bertopic = cast(
            BERTopicModule, install_stub_module("bertopic", _BERTopicModule)
        )


__all__ = ["BERTopicModule", "bertopic"]
