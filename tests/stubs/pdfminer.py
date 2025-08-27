"""Stub for :mod:`pdfminer.high_level` used by search module."""

import sys
import types

import pytest

if "pdfminer.high_level" not in sys.modules:
    pm_stub = types.ModuleType("pdfminer.high_level")

    def _missing(*args, **kwargs):
        pytest.skip("pdfminer.six not installed")

    pm_stub.extract_text = _missing
    sys.modules["pdfminer.high_level"] = pm_stub
