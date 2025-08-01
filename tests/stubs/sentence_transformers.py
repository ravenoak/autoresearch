"""Lightweight stub for :mod:`sentence_transformers`."""

import sys
import types


class DummySentenceTransformer:
    def __init__(self, *_, **__):
        pass

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return [[0.0] * 384 for _ in texts]


dummy_st_module = types.ModuleType("sentence_transformers")
dummy_st_module.SentenceTransformer = DummySentenceTransformer
sys.modules.setdefault("sentence_transformers", dummy_st_module)
