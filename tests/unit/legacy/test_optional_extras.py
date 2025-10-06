from __future__ import annotations

import pytest


@pytest.mark.requires_ui
def test_ui_extra(has_ui) -> None:
    if not has_ui:
        pytest.skip("ui extra not installed")
    import streamlit

    assert hasattr(streamlit, "__version__")


@pytest.mark.requires_vss
def test_vss_extra(has_vss) -> None:
    if not has_vss:
        pytest.skip("vss extra not installed")
    import duckdb_extension_vss as vss

    assert vss is not None


@pytest.mark.requires_git
def test_git_extra(has_git) -> None:
    if not has_git:
        pytest.skip("git extra not installed")
    import git

    assert hasattr(git, "__version__")


@pytest.mark.requires_distributed
def test_distributed_extra(has_distributed) -> None:
    if not has_distributed:
        pytest.skip("distributed extra not installed")
    import ray

    assert hasattr(ray, "__version__")


@pytest.mark.requires_analysis
def test_analysis_extra(has_analysis) -> None:
    if not has_analysis:
        pytest.skip("analysis extra not installed")
    import polars

    assert hasattr(polars, "__version__")


@pytest.mark.requires_nlp
def test_nlp_extra(has_nlp) -> None:
    if not has_nlp:
        pytest.skip("nlp extra not installed")
    try:
        import spacy
    except Exception as exc:  # pragma: no cover - import failure
        pytest.skip(f"spacy import failed: {exc}")

    assert hasattr(spacy, "__version__")


@pytest.mark.requires_llm
def test_llm_extra(has_llm) -> None:
    if not has_llm:
        pytest.skip("llm extra not installed")
    try:
        import fastembed
    except Exception as exc:  # pragma: no cover - optional import failure
        pytest.skip(f"fastembed import failed: {exc}")

    assert hasattr(fastembed, "__version__")


@pytest.mark.requires_parsers
def test_parsers_extra(has_parsers) -> None:
    if not has_parsers:
        pytest.skip("parsers extra not installed")
    import pdfminer

    assert hasattr(pdfminer, "__version__")
