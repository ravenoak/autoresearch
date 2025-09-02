import importlib
import sys
import types

import autoresearch.search.context as context


def _make_cfg(enabled: bool) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        search=types.SimpleNamespace(
            context_aware=types.SimpleNamespace(enabled=enabled)
        )
    )


def _reload_ctx(monkeypatch, enabled: bool):
    ctx = importlib.reload(context)
    monkeypatch.setattr(
        "autoresearch.search.context.get_config", lambda: _make_cfg(enabled)
    )
    return ctx


def test_try_imports_disabled(monkeypatch):
    ctx = _reload_ctx(monkeypatch, False)
    assert ctx._try_import_spacy() is False
    assert ctx._try_import_bertopic() is False
    assert ctx._try_import_sentence_transformers() is False


def test_try_import_spacy_success(monkeypatch):
    ctx = _reload_ctx(monkeypatch, True)
    dummy = types.SimpleNamespace(cli=types.SimpleNamespace())
    sys.modules["spacy"] = dummy
    sys.modules["spacy.cli"] = dummy.cli
    try:
        assert ctx._try_import_spacy() is True
    finally:
        sys.modules.pop("spacy", None)
        sys.modules.pop("spacy.cli", None)


def test_try_import_bertopic_success(monkeypatch):
    ctx = _reload_ctx(monkeypatch, True)
    dummy = types.SimpleNamespace(BERTopic=object)
    sys.modules["bertopic"] = dummy
    try:
        assert ctx._try_import_bertopic() is True
    finally:
        sys.modules.pop("bertopic", None)


def test_try_import_sentence_transformers_success(monkeypatch):
    ctx = _reload_ctx(monkeypatch, True)
    dummy = types.SimpleNamespace(TextEmbedding=object)
    sys.modules["fastembed"] = dummy
    try:
        assert ctx._try_import_sentence_transformers() is True
    finally:
        sys.modules.pop("fastembed", None)
