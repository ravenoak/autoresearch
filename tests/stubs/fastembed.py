"""Stub for :mod:`fastembed` used in the test suite."""
import importlib.util
import sys
import types

if importlib.util.find_spec("fastembed") is None and "fastembed" not in sys.modules:
    module = types.ModuleType("fastembed")
    module.TextEmbedding = object
    module.__version__ = "0.0"
    sys.modules["fastembed"] = module
