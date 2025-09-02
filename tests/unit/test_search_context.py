import importlib
import sys
import types

import pytest

pytestmark = pytest.mark.requires_nlp


def test_optional_dependencies_not_imported_on_module_load(monkeypatch):
    for name in ("spacy", "bertopic", "fastembed"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    module = importlib.reload(importlib.import_module("autoresearch.search.context"))
    assert not module.SPACY_AVAILABLE
    assert not module.BERTOPIC_AVAILABLE
    assert not module.SENTENCE_TRANSFORMERS_AVAILABLE
    assert "spacy" not in sys.modules
    assert "bertopic" not in sys.modules
    assert "fastembed" not in sys.modules


def test_spacy_loaded_when_needed(monkeypatch):
    for name in ("spacy", "spacy.cli"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    module = importlib.reload(importlib.import_module("autoresearch.search.context"))
    assert not module.SPACY_AVAILABLE

    dummy_cli = types.ModuleType("cli")
    dummy_cli.download = lambda model: None
    dummy_spacy = types.ModuleType("spacy")
    dummy_spacy.load = lambda model: "nlp"
    dummy_spacy.cli = dummy_cli
    monkeypatch.setitem(sys.modules, "spacy", dummy_spacy)
    monkeypatch.setitem(sys.modules, "spacy.cli", dummy_cli)

    ctx = module.SearchContext.new_for_tests()
    assert module.SPACY_AVAILABLE
    assert ctx.nlp == "nlp"


def test_topic_model_imports_when_built(monkeypatch):
    for name in ("spacy", "spacy.cli", "bertopic", "fastembed"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    module = importlib.reload(importlib.import_module("autoresearch.search.context"))
    monkeypatch.setattr(module.SearchContext, "_initialize_nlp", lambda self: None)

    dummy_bertopic = types.ModuleType("bertopic")

    class DummyBERTopic:
        def fit_transform(self, docs):
            return [0 for _ in docs], []

    dummy_bertopic.BERTopic = DummyBERTopic
    monkeypatch.setitem(sys.modules, "bertopic", dummy_bertopic)

    dummy_st = types.ModuleType("fastembed")

    class DummySentenceTransformer:
        pass

    dummy_st.TextEmbedding = DummySentenceTransformer
    monkeypatch.setitem(sys.modules, "fastembed", dummy_st)

    ctx = module.SearchContext.new_for_tests()
    ctx.search_history = [
        {"query": "foo", "results": [{"title": "bar", "snippet": "baz"}]}
    ]

    assert not module.BERTOPIC_AVAILABLE
    assert not module.SENTENCE_TRANSFORMERS_AVAILABLE

    ctx.build_topic_model()

    assert module.BERTOPIC_AVAILABLE
    assert module.SENTENCE_TRANSFORMERS_AVAILABLE
    assert isinstance(ctx.topic_model, DummyBERTopic)
