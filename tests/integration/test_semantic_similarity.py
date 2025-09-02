import importlib
import sys
import types

import numpy as np
import pytest

pytestmark = pytest.mark.requires_nlp


def test_semantic_similarity_uses_sentence_transformer(monkeypatch):
    """Verify semantic similarity uses sentence-transformers when available."""
    sys.modules.pop("sentence_transformers", None)
    core = importlib.reload(importlib.import_module("autoresearch.search.core"))

    class DummySentenceTransformer:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def encode(self, texts):
            if isinstance(texts, str):
                return np.array([1.0, 0.0])
            return np.array([[1.0, 0.0], [0.0, 1.0]])

    dummy_module = types.ModuleType("sentence_transformers")
    dummy_module.SentenceTransformer = DummySentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", dummy_module)

    search = core.Search()
    docs = [{"title": "a"}, {"title": "b"}]
    scores = search.calculate_semantic_similarity("query", docs)
    assert scores == [1.0, 0.5]
    assert core.SENTENCE_TRANSFORMERS_AVAILABLE
    assert isinstance(search.get_sentence_transformer(), DummySentenceTransformer)
