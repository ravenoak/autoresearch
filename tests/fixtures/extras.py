# mypy: ignore-errors
from __future__ import annotations

import importlib.util
from importlib import import_module
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Final

import pytest


from .protocols import ExtraProbe, ModuleLoader


def _module_available(name: str) -> bool:
    """Return ``True`` when :mod:`name` can be imported."""

    try:
        spec: ModuleSpec | None = importlib.util.find_spec(name)
    except Exception:  # pragma: no cover - defensive guard for exotic importers
        return False
    return spec is not None


def _load_module(name: str) -> ModuleType | None:
    """Attempt to import ``name`` while suppressing ImportError cascades."""

    try:
        if not _module_available(name):
            return None
        return import_module(name)
    except Exception:  # pragma: no cover - defensive import safety
        return None


def _git_validator(module: ModuleType) -> bool:
    """Verify Git extras expose the expected surface area."""

    repo_attr: Final[object | None] = getattr(module, "Repo", None)
    version_attr: Final[object | None] = getattr(module, "__version__", None)
    return repo_attr is not None and version_attr is not None


EXTRA_PROBES: Final[dict[str, ExtraProbe]] = {
    "ui": ExtraProbe(modules=("streamlit",)),
    "vss": ExtraProbe(modules=("duckdb_extension_vss",)),
    "git": ExtraProbe(modules=("git",), validator=_git_validator),
    "distributed": ExtraProbe(modules=("ray",)),
    "analysis": ExtraProbe(modules=("polars",)),
    "nlp": ExtraProbe(modules=("spacy",)),
    "llm": ExtraProbe(modules=("fastembed",)),
    "parsers": ExtraProbe(modules=("pdfminer",)),
}


def _extra_available(name: str, loader: ModuleLoader = _load_module) -> bool:
    """Helper resolving extras through shared probes."""

    probe = EXTRA_PROBES[name]
    return probe.available(loader)


@pytest.fixture
def has_ui() -> bool:
    """Return True if the UI extra is installed."""
    return _extra_available("ui")


@pytest.fixture
def has_vss() -> bool:
    """Return True if the DuckDB VSS extension is available."""
    return _extra_available("vss")


@pytest.fixture
def has_git() -> bool:
    """Return True if GitPython is installed."""
    return _extra_available("git")


@pytest.fixture
def has_distributed() -> bool:
    """Return True if distributed extras are installed."""
    return _extra_available("distributed")


@pytest.fixture
def has_analysis() -> bool:
    """Return True if analysis extras are installed."""
    return _extra_available("analysis")


@pytest.fixture
def has_nlp() -> bool:
    """Return True if NLP extras are installed."""
    return _extra_available("nlp")


@pytest.fixture
def has_llm() -> bool:
    """Return True if LLM extras are installed."""
    return _extra_available("llm")


@pytest.fixture
def has_parsers() -> bool:
    """Return True if parser extras are installed."""
    return _extra_available("parsers")
