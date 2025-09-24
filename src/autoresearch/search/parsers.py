"""Deterministic document parsers for search backends.

The search stack only promises PDF and DOCX ingestion when the optional
``parsers`` extra is installed. Historically this depended on ad-hoc imports
inside :mod:`autoresearch.search.core`, making failures difficult to reason
about and leading to flaky tests. This module centralises the integration with
``pdfminer.six`` and ``python-docx`` so callers receive consistent text and
clear errors when dependencies are missing or files are corrupt.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Callable

from ..logging_utils import get_logger

log = get_logger(__name__)


class ParserError(RuntimeError):
    """Base exception for document parsing failures."""


class ParserDependencyError(ParserError):
    """Raised when an optional parser dependency is unavailable."""

    def __init__(self, dependency: str, message: str | None = None) -> None:
        detail = message or f"{dependency} is required for document parsing"
        super().__init__(detail)
        self.dependency = dependency


_PDF_EXTRACT: Callable[[str], str] | None = None
_PDF_IMPORT_ERROR: Exception | None = None
_DOCX_LOADER: Callable[[str], object] | None = None
_DOCX_IMPORT_ERROR: Exception | None = None

_WHITESPACE_RE = re.compile(r"\s+")


def _collapse_spaced_letters(text: str) -> str:
    """Merge sequences of single-character tokens into words."""

    tokens = text.split(" ")
    collapsed: list[str] = []
    buffer: list[str] = []
    for token in tokens:
        if not token:
            continue
        if len(token) == 1 and token.isalnum():
            buffer.append(token)
            continue
        if buffer:
            collapsed.append("".join(buffer))
            buffer = []
        collapsed.append(token)
    if buffer:
        collapsed.append("".join(buffer))
    return " ".join(collapsed)


def _normalize_text(text: str) -> str:
    """Collapse consecutive whitespace and trim surrounding blanks."""

    collapsed = text.replace("\r\n", "\n").replace("\r", "\n")
    collapsed = collapsed.replace("\u00a0", " ")
    parts = []
    for line in collapsed.splitlines():
        cleaned = _WHITESPACE_RE.sub(" ", line).strip()
        if cleaned:
            parts.append(cleaned)
    normalized = " ".join(parts).strip()
    if not normalized:
        return normalized
    return _collapse_spaced_letters(normalized)


def _load_pdfminer() -> Callable[..., str]:
    """Return ``pdfminer.six``'s ``extract_text`` helper or raise on failure."""

    global _PDF_EXTRACT, _PDF_IMPORT_ERROR
    if _PDF_EXTRACT is not None:
        return _PDF_EXTRACT
    if _PDF_IMPORT_ERROR is not None:
        raise ParserDependencyError("pdfminer-six", str(_PDF_IMPORT_ERROR)) from _PDF_IMPORT_ERROR
    try:  # pragma: no cover - lazy import exercised in tests
        from pdfminer.high_level import extract_text as pdfminer_extract
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        _PDF_IMPORT_ERROR = exc
        raise ParserDependencyError("pdfminer-six") from exc
    except Exception as exc:  # pragma: no cover - unexpected import error
        _PDF_IMPORT_ERROR = exc
        raise ParserDependencyError("pdfminer-six", str(exc)) from exc
    _PDF_EXTRACT = pdfminer_extract
    return pdfminer_extract


def _load_docx_loader() -> Callable[[str], object]:
    """Return ``python-docx``'s ``Document`` factory or raise on failure."""

    global _DOCX_LOADER, _DOCX_IMPORT_ERROR
    if _DOCX_LOADER is not None:
        return _DOCX_LOADER
    if _DOCX_IMPORT_ERROR is not None:
        raise ParserDependencyError("python-docx", str(_DOCX_IMPORT_ERROR)) from _DOCX_IMPORT_ERROR
    try:  # pragma: no cover - lazy import exercised in tests
        from docx import Document as loader
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        _DOCX_IMPORT_ERROR = exc
        raise ParserDependencyError("python-docx") from exc
    except Exception as exc:  # pragma: no cover - unexpected import error
        _DOCX_IMPORT_ERROR = exc
        raise ParserDependencyError("python-docx", str(exc)) from exc
    _DOCX_LOADER = loader
    return loader


def extract_pdf_text(path: str | Path) -> str:
    """Extract normalized text from a PDF file.

    Args:
        path: Filesystem path to the PDF.

    Returns:
        The normalized text content of the document.

    Raises:
        ParserDependencyError: If ``pdfminer.six`` is not installed.
        ParserError: If the file cannot be parsed or yields no text.
    """

    pdfminer_extract = _load_pdfminer()
    laparams = None
    try:  # pragma: no cover - optional tuning exercised in tests
        from pdfminer.layout import LAParams  # type: ignore

        laparams = LAParams(word_margin=0.1, char_margin=2.0, line_margin=0.5)
    except Exception:  # pragma: no cover - fallback when layout module missing
        laparams = None
    try:
        if laparams is None:
            text = pdfminer_extract(str(path))
        else:
            text = pdfminer_extract(str(path), laparams=laparams)
    except Exception as exc:  # pragma: no cover - parser failure path tested
        raise ParserError(f"Failed to parse PDF {path}: {exc}") from exc
    normalized = _normalize_text(text)
    if not normalized:
        raise ParserError(f"PDF {path} produced no extractable text")
    return normalized


def extract_docx_text(path: str | Path) -> str:
    """Extract normalized text from a DOCX file.

    Args:
        path: Filesystem path to the DOCX document.

    Returns:
        The normalized text content of the document.

    Raises:
        ParserDependencyError: If ``python-docx`` is not installed.
        ParserError: If the file cannot be parsed or yields no text.
    """

    loader = _load_docx_loader()
    try:
        doc = loader(str(path))
    except Exception as exc:  # pragma: no cover - parser failure path tested
        raise ParserError(f"Failed to parse DOCX {path}: {exc}") from exc
    paragraphs = []
    for paragraph in getattr(doc, "paragraphs", []):
        paragraphs.append(paragraph.text)
    text = "\n".join(paragraphs)
    normalized = _normalize_text(text)
    if not normalized:
        raise ParserError(f"DOCX {path} produced no extractable text")
    return normalized


def read_document_text(path: str | Path) -> str:
    """Extract normalized text from supported document formats.

    Args:
        path: Filesystem path to the document.

    Returns:
        The normalized text content of the document.

    Raises:
        ParserError: If the file type is unsupported or cannot be parsed.
    """

    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(file_path)
    if suffix == ".docx":
        return extract_docx_text(file_path)
    if suffix == ".doc":
        raise ParserError("Binary .doc files are not supported; convert to DOCX")
    try:
        raw_text = file_path.read_text(errors="ignore")
    except Exception as exc:  # pragma: no cover - unexpected I/O failure
        raise ParserError(f"Failed to read text file {file_path}: {exc}") from exc
    normalized = _normalize_text(raw_text)
    if not normalized:
        log.debug("Skipping empty text document: %s", file_path)
    return normalized


__all__ = [
    "ParserError",
    "ParserDependencyError",
    "extract_docx_text",
    "extract_pdf_text",
    "read_document_text",
]
