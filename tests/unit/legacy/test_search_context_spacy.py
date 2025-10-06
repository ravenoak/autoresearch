import importlib
import sys
import types

import pytest

pytestmark = pytest.mark.requires_nlp


def _install_dummy_spacy(monkeypatch, load_behavior):
    """Install a minimal spaCy stub with controllable load behavior."""
    dummy_cli = types.ModuleType("cli")
    download_calls = []

    def download(model: str) -> None:
        download_calls.append(model)

    setattr(dummy_cli, "download", download)

    class DummySpacy(types.ModuleType):
        def __init__(self) -> None:
            super().__init__("spacy")
            self.cli = dummy_cli
            self.load_calls = 0

        def load(self, model: str):
            self.load_calls += 1
            return load_behavior(self, model)

    dummy_spacy = DummySpacy()
    monkeypatch.setitem(sys.modules, "spacy", dummy_spacy)
    monkeypatch.setitem(sys.modules, "spacy.cli", dummy_cli)
    return dummy_spacy, download_calls


def test_initialize_nlp_no_auto_download(monkeypatch):
    """spaCy load failure without auto-download leaves NLP unset."""
    for name in ("spacy", "spacy.cli"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.delenv("AUTORESEARCH_AUTO_DOWNLOAD_SPACY_MODEL", raising=False)
    module = importlib.reload(importlib.import_module("autoresearch.search.context"))

    def load_behavior(_self, _model):
        raise OSError("missing model")

    _install_dummy_spacy(monkeypatch, load_behavior)
    ctx = module.SearchContext.new_for_tests()
    assert ctx.nlp is None


def test_initialize_nlp_downloads_when_env(monkeypatch):
    """Auto-download path loads model after download."""
    for name in ("spacy", "spacy.cli"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setenv("AUTORESEARCH_AUTO_DOWNLOAD_SPACY_MODEL", "true")
    module = importlib.reload(importlib.import_module("autoresearch.search.context"))

    def load_behavior(self, _model):
        if self.load_calls == 1:
            raise OSError("missing model")
        return "nlp"

    dummy_spacy, downloads = _install_dummy_spacy(monkeypatch, load_behavior)
    ctx = module.SearchContext.new_for_tests()
    assert ctx.nlp == "nlp"
    assert downloads == ["en_core_web_sm"]
    assert dummy_spacy.load_calls == 2
