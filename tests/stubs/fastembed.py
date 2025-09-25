"""Typed stub for :mod:`fastembed` used in tests."""

from __future__ import annotations

import importlib.util
from types import ModuleType
from typing import Protocol, cast

from ._registry import install_stub_module


class OnnxTextEmbedding:  # pragma: no cover - marker class
    """Placeholder class to satisfy type-checkers."""


class TextEmbedding:  # pragma: no cover - marker class
    """Placeholder class for the dense embedding API."""


class SparseTextEmbedding:  # pragma: no cover - marker class
    """Placeholder class for sparse text embeddings."""


class SparseEmbedding:  # pragma: no cover - marker class
    """Placeholder class for sparse embeddings."""


class ImageEmbedding:  # pragma: no cover - marker class
    """Placeholder class for image embeddings."""


class LateInteractionTextEmbedding:  # pragma: no cover - marker class
    """Placeholder class for late interaction text embeddings."""


class LateInteractionMultimodalEmbedding:  # pragma: no cover - marker class
    """Placeholder class for multimodal embeddings."""


class FastEmbedModule(Protocol):
    OnnxTextEmbedding: type[OnnxTextEmbedding]
    TextEmbedding: type[TextEmbedding]
    SparseTextEmbedding: type[SparseTextEmbedding]
    SparseEmbedding: type[SparseEmbedding]
    ImageEmbedding: type[ImageEmbedding]
    LateInteractionTextEmbedding: type[LateInteractionTextEmbedding]
    LateInteractionMultimodalEmbedding: type[LateInteractionMultimodalEmbedding]
    __version__: str


class _FastEmbedModule(ModuleType):
    OnnxTextEmbedding = OnnxTextEmbedding
    TextEmbedding = TextEmbedding
    SparseTextEmbedding = SparseTextEmbedding
    SparseEmbedding = SparseEmbedding
    ImageEmbedding = ImageEmbedding
    LateInteractionTextEmbedding = LateInteractionTextEmbedding
    LateInteractionMultimodalEmbedding = LateInteractionMultimodalEmbedding
    __version__ = "0.0"
    __all__ = [
        "OnnxTextEmbedding",
        "TextEmbedding",
        "SparseTextEmbedding",
        "SparseEmbedding",
        "ImageEmbedding",
        "LateInteractionTextEmbedding",
        "LateInteractionMultimodalEmbedding",
    ]

    def __init__(self) -> None:
        super().__init__("fastembed")


def _factory() -> _FastEmbedModule:
    return _FastEmbedModule()


if importlib.util.find_spec("fastembed") is None:
    fastembed = cast(FastEmbedModule, install_stub_module("fastembed", _factory))
else:  # pragma: no cover - executed when dependency is available
    import fastembed as _fastembed  # pragma: no cover

    fastembed = cast(FastEmbedModule, _fastembed)


__all__ = [
    "FastEmbedModule",
    "ImageEmbedding",
    "LateInteractionMultimodalEmbedding",
    "LateInteractionTextEmbedding",
    "OnnxTextEmbedding",
    "SparseEmbedding",
    "SparseTextEmbedding",
    "TextEmbedding",
    "fastembed",
]
