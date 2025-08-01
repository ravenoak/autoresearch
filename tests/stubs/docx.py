"""Stub for the :mod:`docx` package."""

import sys
import types

if "docx" not in sys.modules:
    docx_stub = types.ModuleType("docx")
    docx_stub.Document = object
    sys.modules["docx"] = docx_stub
