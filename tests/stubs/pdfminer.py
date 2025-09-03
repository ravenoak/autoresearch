"""Stub for the :mod:`pdfminer` package."""

from __future__ import annotations

import sys
from types import ModuleType


if "pdfminer" not in sys.modules:
    high_level = ModuleType("pdfminer.high_level")

    def extract_text(*args, **kwargs):
        return ""

    high_level.extract_text = extract_text
    module = ModuleType("pdfminer")
    module.high_level = high_level
    module.__version__ = "0.0"
    sys.modules["pdfminer"] = module
    sys.modules["pdfminer.high_level"] = high_level
