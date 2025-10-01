from __future__ import annotations

import importlib.util
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Final

import pytest


def _module_available(name: str) -> bool:
    """Return ``True`` when :mod:`name` can be imported."""

    try:
        spec: ModuleSpec | None = importlib.util.find_spec(name)
    except Exception:  # pragma: no cover - defensive guard for exotic importers
        return False
    return spec is not None


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
    try:
        import git as git_module  # type: ignore[import-untyped]
    except Exception:
        return False
    git_module_typed: ModuleType = git_module
    repo_attr: Final[object | None] = getattr(git_module_typed, "Repo", None)
    version_attr: Final[object | None] = getattr(git_module_typed, "__version__", None)
    return repo_attr is not None and version_attr is not None


@pytest.fixture
def has_distributed() -> bool:
    """Return True if distributed extras are installed."""
    return _module_available("ray")


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
    return _module_available("fastembed")


@pytest.fixture
def has_parsers() -> bool:
    """Return True if parser extras are installed."""
    return _module_available("pdfminer")
