# mypy: ignore-errors
"""Tests for the parsers optional extra."""

from __future__ import annotations

import pytest
import sys

from tests.optional_imports import import_or_skip

from autoresearch.config.loader import get_config, temporary_config
from autoresearch.search.core import _local_file_backend


@pytest.mark.requires_parsers
def test_local_file_backend_docx(tmp_path) -> None:
    """The parsers extra allows reading ``.docx`` files."""
    sys.modules.pop("docx", None)
    docx = import_or_skip("docx")
    doc = docx.Document()
    if not hasattr(doc, "add_paragraph"):
        pytest.skip("python-docx not installed")
    path = tmp_path / "sample.docx"
    doc.add_paragraph("hello world")
    doc.save(path)
    cfg = get_config()
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["docx"]
    with temporary_config(cfg):
        results = _local_file_backend("hello", max_results=1)
    assert isinstance(results, list)
