"""Stub for :mod:`pdfminer.high_level` used by search module."""

import sys
import types

if "pdfminer.high_level" not in sys.modules:
    pm_stub = types.ModuleType("pdfminer.high_level")
    pm_stub.extract_text = lambda *a, **k: ""
    sys.modules["pdfminer.high_level"] = pm_stub
