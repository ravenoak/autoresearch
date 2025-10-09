# mypy: ignore-errors
from __future__ import annotations

from pathlib import Path

import pytest

from tests.optional_imports import import_or_skip


@pytest.fixture
def sample_pdf_file(tmp_path: Path) -> Path:
    """Create a minimal PDF containing known text."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_bytes = (
        b"%PDF-1.2\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/Resources<<>>/MediaBox[0 0 612 792]/"
        b"Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        b"BT /F1 24 Tf 100 700 Td (hello from pdf) Tj ET\n"
        b"endstream\n"
        b"endobj\n"
        b"trailer<</Root 1 0 R>>\n"
        b"%%EOF"
    )
    pdf_path.write_bytes(pdf_bytes)
    return pdf_path


@pytest.fixture
def sample_docx_file(tmp_path: Path) -> Path:
    """Create a DOCX file containing known text."""
    docx = import_or_skip("docx")
    path = tmp_path / "sample.docx"
    try:
        doc = docx.Document()
        # Try the standard API first
        doc.add_paragraph("hello from docx")
        doc.save(path)
    except (AttributeError, ImportError, Exception):
        # If API is broken or library has issues, skip the test
        pytest.skip("python-docx library is not working properly", allow_module_level=False)
    return path
