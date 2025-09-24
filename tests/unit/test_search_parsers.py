from __future__ import annotations

import pytest

from autoresearch.config.loader import get_config, temporary_config
from autoresearch.search import Search
from autoresearch.search.core import _local_file_backend
from autoresearch.search.parsers import ParserError, extract_docx_text, extract_pdf_text
import tests.fixtures.parsers as _parsers  # noqa: F401


@pytest.mark.requires_parsers
def test_extract_pdf_text(sample_pdf_file, tmp_path):
    """Verify PDF text extraction via the local_file backend."""
    text = extract_pdf_text(sample_pdf_file)
    assert "hello" in text
    assert "from" in text
    assert "pdf" in text
    cfg = get_config()
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["pdf"]
    with temporary_config(cfg):
        results = _local_file_backend("hello", max_results=1)
    assert results
    snippet = results[0]["snippet"].lower()
    assert "hello" in snippet
    assert "pdf" in snippet


@pytest.mark.requires_parsers
def test_extract_docx_text(sample_docx_file, tmp_path):
    """Verify DOCX text extraction via the local_file backend."""
    assert extract_docx_text(sample_docx_file) == "hello from docx"
    cfg = get_config()
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["docx"]
    with temporary_config(cfg):
        results = _local_file_backend("hello", max_results=1)
    assert results and "hello from docx" in results[0]["snippet"].lower()


@pytest.mark.requires_parsers
def test_search_local_file_backend(tmp_path, sample_pdf_file, sample_docx_file):
    """Ensure Search.external_lookup finds content in PDF and DOCX files."""
    (tmp_path / "broken.pdf").write_bytes(b"not a pdf")
    cfg = get_config()
    cfg.search.backends = ["local_file"]
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["pdf", "docx"]
    with temporary_config(cfg):
        results = Search.external_lookup("hello", max_results=5)
    snippets = " ".join(r["snippet"].lower() for r in results)
    assert "hello" in snippets
    assert "pdf" in snippets
    assert "hello from docx" in snippets


@pytest.mark.requires_parsers
def test_pdf_parser_errors_on_corrupt_file(tmp_path):
    """PDF parser raises ParserError when the document is unreadable."""
    pdf_path = tmp_path / "corrupt.pdf"
    pdf_path.write_bytes(b"not a real pdf")
    with pytest.raises(ParserError):
        extract_pdf_text(pdf_path)


@pytest.mark.requires_parsers
def test_docx_parser_errors_on_corrupt_file(tmp_path):
    """DOCX parser raises ParserError when the document is unreadable."""
    docx_path = tmp_path / "corrupt.docx"
    docx_path.write_bytes(b"not a real docx")
    with pytest.raises(ParserError):
        extract_docx_text(docx_path)
