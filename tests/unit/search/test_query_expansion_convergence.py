import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import autoresearch.search.context as ctx
import autoresearch.search.core as search_core
from autoresearch.search.context import SearchContext
from autoresearch.search.core import Search
from tests.helpers import make_config_model
from __future__ import annotations

import sys
from collections.abc import Sequence
from types import ModuleType, SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest

from autoresearch.search import context as ctx
from autoresearch.search import core as search_core
from autoresearch.search.context import SearchContext
from autoresearch.search.core import Search
from tests.helpers import make_config_model


@patch(
    "autoresearch.search.context.get_config",
    lambda: make_config_model(
        context_overrides={
            "enabled": True,
            "max_history_items": 5,
            "use_search_history": True,
            "use_query_expansion": True,
            "expansion_factor": 1.0,
        }
    ),
)
def test_query_expansion_converges() -> None:
    """Assume repeated query expansion stabilizes once entity counts stop changing.

    After recording a single query and its entities, expanding the same query twice
    yields identical results, demonstrating convergence of the expansion process.
    """
    with SearchContext.temporary_instance() as ctx:
        ctx.add_to_history("alpha", [{"title": "beta", "snippet": "gamma"}])
        first = ctx.expand_query("delta")
        second = ctx.expand_query("delta")
        assert first == second


def test_reset_instance_creates_new_singleton() -> None:
    """Assume SearchContext enforces a singleton; resetting replaces it.

    After calling reset_instance a subsequent get_instance returns a new object,
    confirming the singleton can be cleared for isolated tests.
    """
    first = SearchContext.get_instance()
    SearchContext.reset_instance()
    second = SearchContext.get_instance()
    assert first is not second


@patch("autoresearch.search.context.SPACY_AVAILABLE", True)
def test_extract_entities_with_spacy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Assume spaCy is available to tag entities.

    A dummy nlp object exposes a single ORG entity, which increments the
    entities counter when _extract_entities runs.
    """
    dummy_ent = SimpleNamespace(text="Acme", label_="ORG")

    def dummy_nlp(text: str) -> SimpleNamespace:
        return SimpleNamespace(ents=[dummy_ent])
    ctx = SearchContext.new_for_tests()
    ctx.nlp = cast(Any, dummy_nlp)
    ctx._extract_entities("Acme")
    assert ctx.entities["acme"] == 1


def test_build_topic_model_with_insufficient_docs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assume topic modeling requires at least two documents.

    With only one query recorded, build_topic_model leaves topic_model unset,
    confirming the guard against sparse history.
    """
    cfg = make_config_model(context_overrides={"enabled": True})
    monkeypatch.setattr(
        "autoresearch.search.context.get_config", lambda: cfg
    )
    with SearchContext.temporary_instance() as ctx:
        ctx.search_history = [{"query": "solo", "results": []}]
        ctx.build_topic_model()
        assert ctx.topic_model is None


def test_try_imports_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Assume optional NLP libraries stay unloaded when context is off.

    Disabling context-aware search causes all import helpers to return False
    without altering availability flags.
    """
    cfg = make_config_model(context_overrides={"enabled": False})
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


def test_try_import_sentence_transformers_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assume sentence-transformers loads when dependencies are present.

    Injecting a dummy module simulates a successful import and flips the
    availability flag to True.
    """
    cfg = make_config_model(context_overrides={"enabled": True})
    monkeypatch.setattr(ctx, "get_config", lambda: cfg)

    class DummyST:
        pass
    dummy_mod = SimpleNamespace(OnnxTextEmbedding=DummyST, TextEmbedding=DummyST)
    monkeypatch.setitem(sys.modules, "fastembed", dummy_mod)
    ctx.SentenceTransformer = None
    ctx.SENTENCE_TRANSFORMERS_AVAILABLE = False
    assert ctx._try_import_sentence_transformers()
    assert ctx.SENTENCE_TRANSFORMERS_AVAILABLE


def test_search_embedding_protocol_prefers_embed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assume fastembed-style classes are accepted via the embedding protocol."""

    cfg = make_config_model()
    search_module = cast(Any, search_core)
    monkeypatch.setattr(search_module, "_get_runtime_config", lambda: cfg)
    monkeypatch.setattr(search_module, "SentenceTransformer", None)
    monkeypatch.setattr(search_module, "SENTENCE_TRANSFORMERS_AVAILABLE", False)
    monkeypatch.setattr(search_module, "_SENTENCE_TRANSFORMER_FALLBACK_ATTEMPTED", False)
    monkeypatch.setattr(search_module, "_SENTENCE_TRANSFORMER_FALLBACK_ERROR", None)

    class FakeFastEmbed:
        last_input: object | None = None

        def embed(self, sentences: Sequence[str]) -> list[list[float]]:
            type(self).last_input = sentences
            return [[1.0, 2.0]]

        def encode(self, sentences: Sequence[str]) -> list[list[float]]:  # pragma: no cover - defensive
            raise AssertionError("encode should not be used when embed exists")

    monkeypatch.setattr(
        search_module,
        "_resolve_sentence_transformer_cls",
        lambda: FakeFastEmbed,
    )

    search = Search()
    model = search.get_sentence_transformer()
    assert isinstance(model, FakeFastEmbed)

    embedding = search.compute_query_embedding("theta")
    assert embedding is not None
    assert embedding.tolist() == [1.0, 2.0]
    assert FakeFastEmbed.last_input == ["theta"]


def test_search_embedding_protocol_falls_back_to_encode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assume sentence-transformers fallback loads when fastembed is unavailable."""

    cfg = make_config_model()
    search_module = cast(Any, search_core)
    monkeypatch.setattr(search_module, "_get_runtime_config", lambda: cfg)
    monkeypatch.setattr(search_module, "SentenceTransformer", None)
    monkeypatch.setattr(search_module, "SENTENCE_TRANSFORMERS_AVAILABLE", False)
    monkeypatch.setattr(search_module, "_resolve_sentence_transformer_cls", lambda: None)
    monkeypatch.setattr(search_module, "_SENTENCE_TRANSFORMER_FALLBACK_ATTEMPTED", False)
    monkeypatch.setattr(search_module, "_SENTENCE_TRANSFORMER_FALLBACK_ERROR", None)

    class FakeSentenceTransformer:
        last_input: object | None = None

        def encode(self, sentences: Sequence[str]) -> list[list[float]]:
            type(self).last_input = sentences
            return [[3.0, 4.0, 5.0]]

    module = ModuleType("sentence_transformers")
    setattr(module, "SentenceTransformer", FakeSentenceTransformer)
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)

    search = Search()
    model = search.get_sentence_transformer()
    assert isinstance(model, FakeSentenceTransformer)

    embedding = search.compute_query_embedding("omega")
    assert embedding is not None
    assert embedding.tolist() == [3.0, 4.0, 5.0]
    assert FakeSentenceTransformer.last_input == ["omega"]


def test_search_sentence_transformer_fallback_cached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assume the sentence-transformers fallback caches the imported class once."""

    cfg = make_config_model()
    search_module = cast(Any, search_core)
    monkeypatch.setattr(search_module, "_get_runtime_config", lambda: cfg)
    monkeypatch.setattr(search_module, "SentenceTransformer", None)
    monkeypatch.setattr(search_module, "SENTENCE_TRANSFORMERS_AVAILABLE", False)
    monkeypatch.setattr(search_module, "_SENTENCE_TRANSFORMER_FALLBACK_ATTEMPTED", False)
    monkeypatch.setattr(search_module, "_SENTENCE_TRANSFORMER_FALLBACK_ERROR", None)

    fastembed_mod = ModuleType("fastembed")
    fastembed_text_mod = ModuleType("fastembed.text")
    monkeypatch.setitem(sys.modules, "fastembed", fastembed_mod)
    monkeypatch.setitem(sys.modules, "fastembed.text", fastembed_text_mod)
    monkeypatch.setattr(
        search_module,
        "_resolve_sentence_transformer_cls",
        search_core._resolve_sentence_transformer_cls,
    )

    class DummySentenceTransformer:
        last_input: object | None = None

        def encode(self, sentences: Sequence[str]) -> list[list[float]]:
            type(self).last_input = sentences
            return [[9.0, 8.0]]

    module = ModuleType("sentence_transformers")
    setattr(module, "SentenceTransformer", DummySentenceTransformer)
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)

    search = Search()
    embedding = search.compute_query_embedding("fallback query")

    assert embedding is not None
    assert embedding.tolist() == [9.0, 8.0]
    assert DummySentenceTransformer.last_input == ["fallback query"]
    assert search_core.SENTENCE_TRANSFORMERS_AVAILABLE
    assert search_core._SENTENCE_TRANSFORMER_FALLBACK_ATTEMPTED
    assert search_core._SENTENCE_TRANSFORMER_FALLBACK_ERROR is None


def test_search_embedding_backend_switches_without_reset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assume swapping embedding providers flushes cached instances automatically."""

    cfg = make_config_model()
    search_module = cast(Any, search_core)
    monkeypatch.setattr(search_module, "_get_runtime_config", lambda: cfg)
    monkeypatch.setattr(search_module, "SENTENCE_TRANSFORMERS_AVAILABLE", False)
    monkeypatch.setattr(search_module, "SentenceTransformer", None)
    monkeypatch.setattr(search_module, "_SENTENCE_TRANSFORMER_FALLBACK_ATTEMPTED", False)
    monkeypatch.setattr(search_module, "_SENTENCE_TRANSFORMER_FALLBACK_ERROR", None)

    class FakeFastEmbed:
        def embed(self, sentences: Sequence[str]) -> list[list[float]]:
            return [[1.0]]

        def encode(self, sentences: Sequence[str]) -> list[list[float]]:  # pragma: no cover - defensive
            raise AssertionError("encode should not run for fastembed fakes")

    class FakeSentenceTransformer:
        def encode(self, sentences: Sequence[str]) -> list[list[float]]:
            return [[2.0]]

    monkeypatch.setattr(
        search_module,
        "_resolve_sentence_transformer_cls",
        lambda: FakeFastEmbed,
    )

    search = Search()
    first_model = search.get_sentence_transformer()
    assert isinstance(first_model, FakeFastEmbed)

    module = ModuleType("sentence_transformers")
    setattr(module, "SentenceTransformer", FakeSentenceTransformer)
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)
    monkeypatch.setattr(search_module, "SentenceTransformer", None)
    monkeypatch.setattr(search_module, "SENTENCE_TRANSFORMERS_AVAILABLE", False)
    monkeypatch.setattr(search_module, "_resolve_sentence_transformer_cls", lambda: None)

    second_model = search.get_sentence_transformer()
    assert isinstance(second_model, FakeSentenceTransformer)
    assert second_model is not first_model
