import importlib
import sys
import types

import pytest


@pytest.mark.requires_parsers
def test_local_file_backend_pdf(tmp_path, monkeypatch, config_factory):
    """_local_file_backend should parse PDFs using pdfminer."""
    dummy_pdf = tmp_path / "sample.pdf"
    dummy_pdf.write_text("content")
    stub_pdf = types.SimpleNamespace(extract_text=lambda p: "dummy snippet")
    monkeypatch.setitem(sys.modules, "pdfminer", types.SimpleNamespace(high_level=stub_pdf))
    monkeypatch.setitem(sys.modules, "pdfminer.high_level", stub_pdf)
    from autoresearch.search import core
    importlib.reload(core)

    cfg = config_factory(
        {
            "search": {
                "local_file": {
                    "path": str(tmp_path),
                    "file_types": ["pdf"],
                }
            }
        }
    )
    monkeypatch.setattr(core, "get_config", lambda: cfg)
    results = core._local_file_backend("dummy")
    assert results, "local_file backend should return at least one match"
    assert results[0]["snippet"] == "dummy snippet"
