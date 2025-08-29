from __future__ import annotations

import importlib.util

import pytest


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


@pytest.fixture
def has_ui() -> bool:
    """Return True if the UI extra is installed."""
    return _module_available("streamlit")


@pytest.fixture
def has_vss() -> bool:
    """Return True if the DuckDB VSS extension is available."""
    return _module_available("duckdb_extension_vss")


@pytest.fixture
def has_git() -> bool:
    """Return True if GitPython is installed."""
    return _module_available("git")


@pytest.fixture
def has_analysis() -> bool:
    """Return True if analysis extras are installed."""
    return _module_available("polars")


@pytest.fixture
def has_nlp() -> bool:
    """Return True if NLP extras are installed."""
    return _module_available("spacy")


@pytest.fixture
def has_llm() -> bool:
    """Return True if LLM extras are installed."""
    return _module_available("transformers")


@pytest.fixture
def has_parsers() -> bool:
    """Return True if parser extras are installed."""
    return _module_available("pdfminer")
