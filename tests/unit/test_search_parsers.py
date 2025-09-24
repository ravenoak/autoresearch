from __future__ import annotations

import builtins
import contextlib
import sys
from types import ModuleType

import pytest

from autoresearch.config.loader import get_config, temporary_config
from autoresearch.search import Search
from autoresearch.search.core import _local_file_backend
from autoresearch.search.parsers import (
    ParserDependencyError,
    ParserError,
    extract_docx_text,
    extract_pdf_text,
    read_document_text,
)
import autoresearch.search.parsers as parser_module
import tests.fixtures.parsers as _parsers  # noqa: F401


@contextlib.contextmanager
def _block_optional_dependency(monkeypatch: pytest.MonkeyPatch, prefix: str):
    """Temporarily raise ``ModuleNotFoundError`` for an optional dependency."""

    removed: dict[str, ModuleType] = {}
    for name in list(sys.modules):
        if name == prefix or name.startswith(f"{prefix}."):
            removed[name] = sys.modules.pop(name)

    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> ModuleType:
        if name == prefix or name.startswith(f"{prefix}."):
            raise ModuleNotFoundError(prefix)
        return original_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setitem(builtins.__dict__, "__import__", fake_import)
    try:
        yield
    finally:
        sys.modules.update(removed)


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


@pytest.mark.requires_parsers
def test_extract_pdf_text_requires_dependency(monkeypatch, tmp_path):
    """PDF parser reports missing pdfminer through ParserDependencyError."""

    pdf_path = tmp_path / "stub.pdf"
    pdf_path.write_bytes(b"%PDF-1.2\n")
    monkeypatch.setattr(parser_module, "_PDF_EXTRACT", None, raising=False)
    monkeypatch.setattr(parser_module, "_PDF_IMPORT_ERROR", None, raising=False)

    with _block_optional_dependency(monkeypatch, "pdfminer"):
        with pytest.raises(ParserDependencyError) as exc_info:
            extract_pdf_text(pdf_path)

    assert "pdfminer" in str(exc_info.value).lower()


@pytest.mark.requires_parsers
def test_extract_docx_text_requires_dependency(monkeypatch, tmp_path):
    """DOCX parser reports missing python-docx dependencies."""

    docx_path = tmp_path / "stub.docx"
    docx_path.write_bytes(b"PK\x03\x04")
    monkeypatch.setattr(parser_module, "_DOCX_LOADER", None, raising=False)
    monkeypatch.setattr(parser_module, "_DOCX_IMPORT_ERROR", None, raising=False)

    with _block_optional_dependency(monkeypatch, "docx"):
        with pytest.raises(ParserDependencyError) as exc_info:
            extract_docx_text(docx_path)

    assert "python-docx" in str(exc_info.value).lower()


@pytest.mark.requires_parsers
def test_read_document_text_normalizes_plain_text(tmp_path):
    """Plain text files are normalized for deterministic snippets."""

    text_path = tmp_path / "notes.txt"
    text_path.write_text("Hello   world\n\nSecond   line  ")

    normalized = read_document_text(text_path)
    assert normalized == "Hello world Second line"


@pytest.mark.requires_parsers
def test_read_document_text_rejects_doc_files(tmp_path):
    """Binary .doc files raise ParserError so callers can skip them."""

    doc_path = tmp_path / "legacy.doc"
    doc_path.write_text("fake doc content")

    with pytest.raises(ParserError) as exc_info:
        read_document_text(doc_path)

    assert "convert to docx" in str(exc_info.value).lower()
