# mypy: ignore-errors
import importlib
import sys
import types

import autoresearch.search.context as context
from tests.helpers import ConfigModelStub, make_config_model


def _make_cfg(enabled: bool) -> ConfigModelStub:
    return make_config_model(context_overrides={"enabled": enabled})


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
    dummy = types.ModuleType("spacy")
    cli = types.ModuleType("cli")
    setattr(dummy, "cli", cli)
    sys.modules["spacy"] = dummy
    sys.modules["spacy.cli"] = cli
    try:
        assert ctx._try_import_spacy() is True
    finally:
        sys.modules.pop("spacy", None)
        sys.modules.pop("spacy.cli", None)


def test_try_import_bertopic_success(monkeypatch):
    ctx = _reload_ctx(monkeypatch, True)
    dummy = types.ModuleType("bertopic")
    setattr(dummy, "BERTopic", object)
    sys.modules["bertopic"] = dummy
    try:
        assert ctx._try_import_bertopic() is True
    finally:
        sys.modules.pop("bertopic", None)


def test_try_import_sentence_transformers_success(monkeypatch):
    ctx = _reload_ctx(monkeypatch, True)
    dummy = types.ModuleType("fastembed")
    setattr(dummy, "OnnxTextEmbedding", object)
    setattr(dummy, "TextEmbedding", object)
    sys.modules["fastembed"] = dummy
    try:
        assert ctx._try_import_sentence_transformers() is True
    finally:
        sys.modules.pop("fastembed", None)
