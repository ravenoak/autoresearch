from __future__ import annotations

import pytest

from autoresearch.config.loader import get_config, temporary_config
from autoresearch.search import Search
from autoresearch.search.core import _local_file_backend
import tests.fixtures.parsers as _parsers  # noqa: F401


@pytest.mark.requires_parsers
@pytest.mark.xfail(reason="PDF parser backend flaky in CI")
def test_extract_pdf_text(sample_pdf_file, tmp_path):
    """Verify PDF text extraction via the local_file backend."""
    cfg = get_config()
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["pdf"]
    with temporary_config(cfg):
        results = _local_file_backend("hello", max_results=1)
    assert results and "hello from pdf" in results[0]["snippet"].lower()


@pytest.mark.requires_parsers
@pytest.mark.xfail(reason="DOCX parser backend flaky in CI")
def test_extract_docx_text(sample_docx_file, tmp_path):
    """Verify DOCX text extraction via the local_file backend."""
    cfg = get_config()
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["docx"]
    with temporary_config(cfg):
        results = _local_file_backend("hello", max_results=1)
    assert results and "hello from docx" in results[0]["snippet"].lower()


@pytest.mark.requires_parsers
@pytest.mark.xfail(reason="Local file backend pending parser integration")
def test_search_local_file_backend(tmp_path, sample_pdf_file, sample_docx_file):
    """Ensure Search.external_lookup finds content in PDF and DOCX files."""
    cfg = get_config()
    cfg.search.backends = ["local_file"]
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["pdf", "docx"]
    with temporary_config(cfg):
        results = Search.external_lookup("hello", max_results=5)
    snippets = " ".join(r["snippet"].lower() for r in results)
    assert "hello from pdf" in snippets
    assert "hello from docx" in snippets
