"""Stub for :mod:`fastembed` used in the test suite."""
import importlib.util
import sys
import types

if importlib.util.find_spec("fastembed") is None and "fastembed" not in sys.modules:
    module = types.ModuleType("fastembed")
    module.OnnxTextEmbedding = object
    module.TextEmbedding = object
    module.SparseTextEmbedding = object
    module.SparseEmbedding = object
    module.ImageEmbedding = object
    module.LateInteractionTextEmbedding = object
    module.LateInteractionMultimodalEmbedding = object
    module.__version__ = "0.0"
    module.__all__ = [
        "OnnxTextEmbedding",
        "TextEmbedding",
        "SparseTextEmbedding",
        "SparseEmbedding",
        "ImageEmbedding",
        "LateInteractionTextEmbedding",
        "LateInteractionMultimodalEmbedding",
    ]
    sys.modules["fastembed"] = module
