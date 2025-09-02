"""Stub for :mod:`fastembed` used in the test suite."""
import sys
import types

module = types.ModuleType("fastembed")
module.TextEmbedding = object
module.__version__ = "0.0"
sys.modules.setdefault("fastembed", module)
