"""Stub for the :mod:`docx` package."""

import sys
import types

import pytest

if "docx" not in sys.modules:
    docx_stub = types.ModuleType("docx")

    class _MissingDoc:
        def __init__(self, *args, **kwargs):
            pytest.skip("python-docx not installed")

    docx_stub.Document = _MissingDoc
    sys.modules["docx"] = docx_stub
