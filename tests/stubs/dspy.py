"""Stub for :mod:`dspy` used in tests."""
import importlib.util
import sys
import types

if importlib.util.find_spec("dspy") is None and "dspy" not in sys.modules:
    module = types.ModuleType("dspy")
    module.__version__ = "0.0"
    sys.modules["dspy"] = module
