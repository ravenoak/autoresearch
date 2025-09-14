from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.requires_gpu
def test_bertopic_integration(monkeypatch):
    """BERTopic integration activates when GPU extras are available."""
    bertopic = pytest.importorskip("bertopic")
    from autoresearch.search import context

    monkeypatch.setattr(
        context,
        "get_config",
        lambda: SimpleNamespace(
            search=SimpleNamespace(context_aware=SimpleNamespace(enabled=True))
        ),
    )
    if not context._try_import_bertopic():  # pragma: no cover - import issues
        pytest.skip("BERTopic import failed")
    assert bertopic.BERTopic is context.BERTopic


@pytest.mark.requires_parsers
def test_docx_backend_search(tmp_path, monkeypatch):
    """Local file backend indexes DOCX files when parsers extras are installed."""
    docx = pytest.importorskip("docx")
    from autoresearch.search import core

    doc_path = tmp_path / "example.docx"
    doc = docx.Document()
    if not hasattr(doc, "add_paragraph"):
        pytest.skip("docx package lacks add_paragraph")
    doc.add_paragraph("hello world")
    doc.save(doc_path)
    cfg = SimpleNamespace(
        search=SimpleNamespace(local_file=SimpleNamespace(path=str(tmp_path), file_types=["docx"]))
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    results = core._local_file_backend("hello", max_results=1)
    assert results and results[0]["title"] == "example.docx"
