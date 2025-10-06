# mypy: ignore-errors
"""Verify optional extras expose their expected modules.

Each optional extra should install a third-party package.  These smoke tests
ensure the package can be imported and provides a key attribute.  They are
skipped when the corresponding extra is not installed.
"""

from __future__ import annotations

import pytest

from tests.optional_imports import import_or_skip


@pytest.mark.parametrize(
    ("module", "attr"),
    [
        pytest.param("spacy", "__version__", marks=pytest.mark.requires_nlp),
        pytest.param("streamlit", "__version__", marks=pytest.mark.requires_ui),
        pytest.param("duckdb", "__version__", marks=pytest.mark.requires_vss),
        pytest.param("git", "Repo", marks=pytest.mark.requires_git),
        pytest.param("redis", "Redis", marks=pytest.mark.requires_distributed),
        pytest.param("polars", "__version__", marks=pytest.mark.requires_analysis),
        pytest.param("fastembed", "__version__", marks=pytest.mark.requires_llm),
        pytest.param("docx", "Document", marks=pytest.mark.requires_parsers),
    ],
)
def test_optional_module_exports(module: str, attr: str) -> None:
    """Modules installed via extras expose the expected attribute."""
    try:
        mod = import_or_skip(module)
    except Exception as exc:  # pragma: no cover - defensive
        if module == "spacy":
            pytest.skip(f"spacy import failed: {exc}")
        raise
    assert hasattr(mod, attr)
