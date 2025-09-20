from types import SimpleNamespace
from unittest.mock import patch

import autoresearch.search.context as ctx
import sys
from autoresearch.search.context import SearchContext


@patch(
    "autoresearch.search.context.get_config",
    lambda: SimpleNamespace(
        search=SimpleNamespace(
            context_aware=SimpleNamespace(
                enabled=True,
                max_history_items=5,
                use_search_history=True,
                use_query_expansion=True,
                expansion_factor=1.0,
            )
        )
    ),
)
def test_query_expansion_converges():
    """Assume repeated query expansion stabilizes once entity counts stop changing.

    After recording a single query and its entities, expanding the same query twice
    yields identical results, demonstrating convergence of the expansion process.
    """
    with SearchContext.temporary_instance() as ctx:
        ctx.add_to_history("alpha", [{"title": "beta", "snippet": "gamma"}])
        first = ctx.expand_query("delta")
        second = ctx.expand_query("delta")
        assert first == second


def test_reset_instance_creates_new_singleton():
    """Assume SearchContext enforces a singleton; resetting replaces it.

    After calling reset_instance a subsequent get_instance returns a new object,
    confirming the singleton can be cleared for isolated tests.
    """
    first = SearchContext.get_instance()
    SearchContext.reset_instance()
    second = SearchContext.get_instance()
    assert first is not second


@patch("autoresearch.search.context.SPACY_AVAILABLE", True)
def test_extract_entities_with_spacy(monkeypatch):
    """Assume spaCy is available to tag entities.

    A dummy nlp object exposes a single ORG entity, which increments the
    entities counter when _extract_entities runs.
    """
    dummy_ent = SimpleNamespace(text="Acme", label_="ORG")

    def dummy_nlp(text):
        return SimpleNamespace(ents=[dummy_ent])
    ctx = SearchContext.new_for_tests()
    ctx.nlp = dummy_nlp
    ctx._extract_entities("Acme")
    assert ctx.entities["acme"] == 1


def test_build_topic_model_with_insufficient_docs(monkeypatch):
    """Assume topic modeling requires at least two documents.

    With only one query recorded, build_topic_model leaves topic_model unset,
    confirming the guard against sparse history.
    """
    cfg = SimpleNamespace(
        search=SimpleNamespace(
            context_aware=SimpleNamespace(enabled=True)
        )
    )
    monkeypatch.setattr(
        "autoresearch.search.context.get_config", lambda: cfg
    )
    with SearchContext.temporary_instance() as ctx:
        ctx.search_history = [{"query": "solo", "results": []}]
        ctx.build_topic_model()
        assert ctx.topic_model is None


def test_try_imports_disabled(monkeypatch):
    """Assume optional NLP libraries stay unloaded when context is off.

    Disabling context-aware search causes all import helpers to return False
    without altering availability flags.
    """
    cfg = SimpleNamespace(search=SimpleNamespace(context_aware=SimpleNamespace(enabled=False)))
    monkeypatch.setattr(ctx, "get_config", lambda: cfg)
    ctx.SPACY_AVAILABLE = False
    ctx.BERTOPIC_AVAILABLE = False
    ctx.SENTENCE_TRANSFORMERS_AVAILABLE = False
    assert not ctx._try_import_spacy()
    assert not ctx._try_import_bertopic()
    assert not ctx._try_import_sentence_transformers()
    assert not ctx.SPACY_AVAILABLE
    assert not ctx.BERTOPIC_AVAILABLE
    assert not ctx.SENTENCE_TRANSFORMERS_AVAILABLE


def test_try_import_sentence_transformers_success(monkeypatch):
    """Assume sentence-transformers loads when dependencies are present.

    Injecting a dummy module simulates a successful import and flips the
    availability flag to True.
    """
    cfg = SimpleNamespace(search=SimpleNamespace(context_aware=SimpleNamespace(enabled=True)))
    monkeypatch.setattr(ctx, "get_config", lambda: cfg)

    class DummyST:
        pass
    dummy_mod = SimpleNamespace(OnnxTextEmbedding=DummyST, TextEmbedding=DummyST)
    monkeypatch.setitem(sys.modules, "fastembed", dummy_mod)
    ctx.SentenceTransformer = None
    ctx.SENTENCE_TRANSFORMERS_AVAILABLE = False
    assert ctx._try_import_sentence_transformers()
    assert ctx.SENTENCE_TRANSFORMERS_AVAILABLE
