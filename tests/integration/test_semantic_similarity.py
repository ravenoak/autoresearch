import importlib
import sys
import types

import numpy as np
import pytest

pytestmark = pytest.mark.requires_nlp


def test_semantic_similarity_uses_fastembed(monkeypatch):
    """Verify semantic similarity uses fastembed when available."""
    sys.modules.pop("fastembed", None)
    core = importlib.reload(importlib.import_module("autoresearch.search.core"))

    class DummyFastEmbed:
        def embed(self, texts):
            if isinstance(texts, list) and len(texts) == 1:
                return [np.array([1.0, 0.0])]
            return [np.array([1.0, 0.0]), np.array([0.0, 1.0])]

    dummy_module = types.ModuleType("fastembed")
    setattr(dummy_module, "OnnxTextEmbedding", lambda: DummyFastEmbed())
    setattr(dummy_module, "TextEmbedding", lambda: DummyFastEmbed())
    monkeypatch.setitem(sys.modules, "fastembed", dummy_module)

    search = core.Search()
    docs = [{"title": "a"}, {"title": "b"}]
    scores = search.calculate_semantic_similarity("query", docs)
    assert scores == [1.0, 0.5]
    assert core.SENTENCE_TRANSFORMERS_AVAILABLE
    assert isinstance(search.get_sentence_transformer(), DummyFastEmbed)


def test_semantic_similarity_legacy_fastembed(monkeypatch):
    """Legacy fastembed builds still work via the TextEmbedding alias."""
    sys.modules.pop("fastembed", None)
    core = importlib.reload(importlib.import_module("autoresearch.search.core"))

    class DummyFastEmbed:
        def embed(self, texts):
            if isinstance(texts, list) and len(texts) == 1:
                return [np.array([1.0, 0.0])]
            return [np.array([1.0, 0.0]), np.array([0.0, 1.0])]

    dummy_module = types.ModuleType("fastembed")
    setattr(dummy_module, "TextEmbedding", lambda: DummyFastEmbed())
    monkeypatch.setitem(sys.modules, "fastembed", dummy_module)

    search = core.Search()
    docs = [{"title": "a"}, {"title": "b"}]
    scores = search.calculate_semantic_similarity("query", docs)
    assert scores == [1.0, 0.5]
    assert core.SENTENCE_TRANSFORMERS_AVAILABLE
    assert isinstance(search.get_sentence_transformer(), DummyFastEmbed)
