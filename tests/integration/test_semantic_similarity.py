import importlib
import sys
import types
from typing import Any, Mapping, Sequence

import numpy as np
import pytest
from numpy.typing import NDArray

pytestmark = pytest.mark.requires_nlp


def test_semantic_similarity_uses_fastembed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify semantic similarity uses fastembed when available."""
    sys.modules.pop("fastembed", None)
    core = importlib.reload(importlib.import_module("autoresearch.search.core"))

    class DummyFastEmbed:
        def embed(self, texts: Sequence[str]) -> list[NDArray[np.floating[Any]]]:
            if len(texts) == 1:
                return [np.array([1.0, 0.0])]
            return [np.array([1.0, 0.0]), np.array([0.0, 1.0])]

    dummy_module = types.ModuleType("fastembed")
    setattr(dummy_module, "OnnxTextEmbedding", DummyFastEmbed)
    setattr(dummy_module, "TextEmbedding", DummyFastEmbed)
    monkeypatch.setitem(sys.modules, "fastembed", dummy_module)

    search = core.Search()
    docs: list[Mapping[str, object]] = [{"title": "a"}, {"title": "b"}]
    scores: list[float] = list(search.calculate_semantic_similarity("query", docs))
    assert scores == [1.0, 0.5]
    assert core.SENTENCE_TRANSFORMERS_AVAILABLE
    assert isinstance(search.get_sentence_transformer(), DummyFastEmbed)


def test_semantic_similarity_legacy_fastembed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy fastembed builds still work via the TextEmbedding alias."""
    sys.modules.pop("fastembed", None)
    core = importlib.reload(importlib.import_module("autoresearch.search.core"))

    class DummyFastEmbed:
        def embed(self, texts: Sequence[str]) -> list[NDArray[np.floating[Any]]]:
            if len(texts) == 1:
                return [np.array([1.0, 0.0])]
            return [np.array([1.0, 0.0]), np.array([0.0, 1.0])]

    dummy_module = types.ModuleType("fastembed")
    setattr(dummy_module, "TextEmbedding", DummyFastEmbed)
    monkeypatch.setitem(sys.modules, "fastembed", dummy_module)

    search = core.Search()
    docs: list[Mapping[str, object]] = [{"title": "a"}, {"title": "b"}]
    scores: list[float] = list(search.calculate_semantic_similarity("query", docs))
    assert scores == [1.0, 0.5]
    assert core.SENTENCE_TRANSFORMERS_AVAILABLE
    assert isinstance(search.get_sentence_transformer(), DummyFastEmbed)
