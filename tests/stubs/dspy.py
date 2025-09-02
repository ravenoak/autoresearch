"""Stub for :mod:`dspy` used in tests."""
import sys
import types

module = types.ModuleType("dspy")
module.__version__ = "0.0"
sys.modules.setdefault("dspy", module)
