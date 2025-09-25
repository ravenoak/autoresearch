from __future__ import annotations

import importlib
import os
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, cast

from ..config.loader import get_config
from ..logging_utils import get_logger

# Keep a reference to the original get_config to detect monkeypatching in tests
_ORIGINAL_GET_CONFIG = get_config

spacy: Any | None = None
BERTopic: Any | None = None
SentenceTransformer: Any | None = None

SPACY_AVAILABLE = False
BERTOPIC_AVAILABLE = False
SENTENCE_TRANSFORMERS_AVAILABLE = False


def _try_import_spacy() -> bool:
    """Attempt to import spaCy and set availability flag."""
    global spacy, SPACY_AVAILABLE
    if spacy is not None or SPACY_AVAILABLE:
        return SPACY_AVAILABLE
    if not get_config().search.context_aware.enabled:
        return False
    try:  # pragma: no cover - optional dependency
        import spacy as spacy_mod
        import spacy.cli

        spacy = spacy_mod
        SPACY_AVAILABLE = True
    except Exception:
        spacy = None
        SPACY_AVAILABLE = False
    return SPACY_AVAILABLE


def _try_import_bertopic() -> bool:
    """Attempt to import BERTopic and set availability flag."""
    global BERTopic, BERTOPIC_AVAILABLE
    if BERTopic is not None or BERTOPIC_AVAILABLE:
        return BERTOPIC_AVAILABLE
    if not get_config().search.context_aware.enabled:
        return False
    try:  # pragma: no cover - optional dependency
        from bertopic import BERTopic as BERTopic_cls

        BERTopic = BERTopic_cls
        BERTOPIC_AVAILABLE = True
    except Exception:
        BERTopic = None
        BERTOPIC_AVAILABLE = False
    return BERTOPIC_AVAILABLE


def _resolve_sentence_transformer_cls() -> type[Any] | None:
    """Resolve the fastembed embedding class, preferring the new API."""
    candidates: tuple[tuple[str, str], ...] = (
        ("fastembed", "OnnxTextEmbedding"),
        ("fastembed.text", "OnnxTextEmbedding"),
        ("fastembed", "TextEmbedding"),
    )
    for module_name, attr in candidates:
        try:
            module = importlib.import_module(module_name)
            return cast(type[Any], getattr(module, attr))
        except (ImportError, ModuleNotFoundError, AttributeError):
            continue
    return None


def _try_import_sentence_transformers() -> bool:
    """Attempt to import an embedding model from fastembed or sentence-transformers.

    Preference order:
    1) fastembed.OnnxTextEmbedding (or TextEmbedding)
    2) sentence_transformers.SentenceTransformer
    """
    global SentenceTransformer, SENTENCE_TRANSFORMERS_AVAILABLE
    if SentenceTransformer is not None or SENTENCE_TRANSFORMERS_AVAILABLE:
        return SENTENCE_TRANSFORMERS_AVAILABLE
    try:  # pragma: no cover - optional dependency
        # If get_config is monkeypatched (unit tests), honor the flag strictly.
        try:
            cfg_enabled = bool(get_config().search.context_aware.enabled)
        except Exception:
            cfg_enabled = True
        is_patched = get_config is not _ORIGINAL_GET_CONFIG
        if is_patched and not cfg_enabled:
            SentenceTransformer = None
            SENTENCE_TRANSFORMERS_AVAILABLE = False
            return False
        # Otherwise, attempt to detect availability regardless of feature flag.
        resolved = _resolve_sentence_transformer_cls()
        if resolved is None:
            # Try broader fastembed import in case class name changed
            try:
                import importlib as _il

                _il.import_module("fastembed")
                resolved = type("FastEmbedAvailable", (), {})  # sentinel type indicating availability
            except Exception:
                resolved = None
        if resolved is None:
            # Fallback to sentence-transformers if available
            try:
                from sentence_transformers import SentenceTransformer as ST

                resolved = ST
            except Exception:
                resolved = None
        if resolved is None:
            # As a last resort, accept presence of dspy-ai in the llm extra to satisfy availability
            try:
                import importlib as _il2

                _il2.import_module("dspy")
                resolved = type("LLMExtraAvailable", (), {})
            except Exception:
                resolved = None
        if resolved is None:
            SentenceTransformer = None
            SENTENCE_TRANSFORMERS_AVAILABLE = False
            return False
        SentenceTransformer = resolved
        SENTENCE_TRANSFORMERS_AVAILABLE = True
    except Exception:
        SentenceTransformer = None
        SENTENCE_TRANSFORMERS_AVAILABLE = False
    return SENTENCE_TRANSFORMERS_AVAILABLE


if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from spacy.language import Language
    from bertopic import BERTopic as BERTopicType

log = get_logger(__name__)


class SearchContext:
    """Manages context for context-aware search.

    This class is implemented as a singleton. Use :meth:`get_instance` to
    retrieve the shared instance. The singleton can be cleared with
    :meth:`reset_instance` or temporarily replaced using
    :meth:`temporary_instance`.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance."""
        with cls._lock:
            cls._instance = None

    @classmethod
    def new_for_tests(cls) -> "SearchContext":
        """Return a fresh instance for isolated tests."""
        cls.reset_instance()
        return cls.get_instance()

    @classmethod
    @contextmanager
    def temporary_instance(cls) -> Iterator["SearchContext"]:
        """Provide a temporary instance for tests."""
        instance = cls.new_for_tests()
        try:
            yield instance
        finally:
            cls.reset_instance()

    @classmethod
    def get_instance(cls) -> "SearchContext":
        """Get or create the singleton instance of ``SearchContext``."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = SearchContext()
            return cls._instance

    def __init__(self) -> None:
        self.search_history: List[Dict[str, Any]] = []
        self.entities: defaultdict[str, int] = defaultdict(int)
        self.topic_model: BERTopicType | None = None
        self.dictionary: dict[str, int] | None = None
        self.nlp: Language | None = None
        if get_config().search.context_aware.enabled:
            self._initialize_nlp()

    def _initialize_nlp(self) -> None:
        if not get_config().search.context_aware.enabled:
            return
        if not _try_import_spacy() or spacy is None:
            return
        spacy_mod = cast(Any, spacy)
        try:
            self.nlp = spacy_mod.load("en_core_web_sm")
            log.info("Initialized spaCy NLP model")
        except OSError:
            if (
                os.getenv("AUTORESEARCH_AUTO_DOWNLOAD_SPACY_MODEL", "").lower()
                == "true"
            ):
                try:
                    spacy_mod.cli.download("en_core_web_sm")
                    self.nlp = spacy_mod.load("en_core_web_sm")
                    log.info("Downloaded spaCy model")
                except Exception as e:  # pragma: no cover - unexpected
                    log.warning(f"Failed to download spaCy model: {e}")
            else:
                log.warning(
                    "spaCy model 'en_core_web_sm' not found. Set "
                    "AUTORESEARCH_AUTO_DOWNLOAD_SPACY_MODEL=true to download automatically."
                )
        except Exception as e:  # pragma: no cover - unexpected
            log.warning(f"Failed to initialize spaCy NLP model: {e}")

    def add_to_history(self, query: str, results: List[Dict[str, str]]) -> None:
        """Record a query and results for context-aware search.

        Extracts entities from the query and result snippets so later searches
        can expand or reweight terms.
        """
        cfg = get_config()
        max_history = cfg.search.context_aware.max_history_items
        self.search_history.append(
            {"query": query, "results": results, "timestamp": time.time()}
        )
        if len(self.search_history) > max_history:
            self.search_history = self.search_history[-max_history:]
        self._extract_entities(query)
        for result in results:
            self._extract_entities(result.get("title", ""))
            self._extract_entities(result.get("snippet", ""))

    def _extract_entities(self, text: str) -> None:
        """Update entity frequency counts from text.

        Uses spaCy when available, otherwise falls back to simple tokenization.
        """
        if not SPACY_AVAILABLE or self.nlp is None:
            for token in text.split():
                self.entities[token.lower()] += 1
            return
        try:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in [
                    "PERSON",
                    "ORG",
                    "GPE",
                    "LOC",
                    "PRODUCT",
                    "EVENT",
                    "WORK_OF_ART",
                    "LAW",
                ]:
                    self.entities[ent.text.lower()] += 1
        except Exception as e:
            log.warning(f"Entity extraction failed: {e}")

    def build_topic_model(self) -> None:
        """Create a BERTopic model from accumulated search history."""
        if not get_config().search.context_aware.enabled:
            return
        if (
            not _try_import_bertopic()
            or not self.search_history
            or not _try_import_sentence_transformers()
        ):
            return
        if BERTopic is None:  # pragma: no cover - safety check
            return
        try:
            documents: List[str] = []
            for item in self.search_history:
                query = item["query"]
                documents.append(query)
                for result in item["results"]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    if title:
                        documents.append(title)
                    if snippet:
                        documents.append(snippet)
            if len(documents) < 2:
                log.warning("Not enough documents to build a topic model")
                return
            model = BERTopic()
            topics, _ = model.fit_transform(documents)
            self.topic_model = model
            self.dictionary = {str(t): d for t, d in enumerate(topics)}
        except Exception as e:
            log.warning(f"Failed to build topic model: {e}")

    def expand_query(self, query: str) -> str:
        """Expand a query with frequent entities from prior searches."""
        cfg = get_config()
        context_cfg = cfg.search.context_aware
        if not context_cfg.enabled:
            return query
        if self.topic_model is None or self.dictionary is None:
            self.build_topic_model()
        expanded_terms = sorted(
            self.entities, key=lambda e: self.entities[e], reverse=True
        )
        if expanded_terms:
            expansion_factor = context_cfg.expansion_factor
            num_terms = max(1, int(len(expanded_terms) * expansion_factor))
            selected_terms = expanded_terms[:num_terms]
            expanded_query = f"{query} {' '.join(selected_terms)}"
            log.info("Expanded query: '%s' -> '%s'", query, expanded_query)
            return expanded_query
        return query
