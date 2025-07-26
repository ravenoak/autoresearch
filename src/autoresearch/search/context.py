from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, TYPE_CHECKING

from ..config import get_config
from ..logging_utils import get_logger

try:
    import spacy
    import spacy.cli

    SPACY_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    spacy = None  # type: ignore[assignment]
    SPACY_AVAILABLE = False

try:
    from bertopic import BERTopic

    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer  # noqa: F401

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from spacy.language import Language
    from bertopic import BERTopic as BERTopicType

log = get_logger(__name__)


class SearchContext:
    """Manages context for context-aware search."""

    _instance = None
    _lock = threading.Lock()

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
        self._initialize_nlp()

    def _initialize_nlp(self) -> None:
        from . import spacy as pkg_spacy, SPACY_AVAILABLE as pkg_SPACY_AVAILABLE

        if not pkg_SPACY_AVAILABLE:
            return
        try:
            self.nlp = pkg_spacy.load("en_core_web_sm")
            log.info("Initialized spaCy NLP model")
        except OSError:
            if (
                os.getenv("AUTORESEARCH_AUTO_DOWNLOAD_SPACY_MODEL", "").lower()
                == "true"
            ):
                try:
                    pkg_spacy.cli.download("en_core_web_sm")
                    self.nlp = pkg_spacy.load("en_core_web_sm")
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
        cfg = get_config()
        max_history = cfg.search.context_aware.max_history_items
        self.search_history.append({"query": query, "results": results, "timestamp": time.time()})
        if len(self.search_history) > max_history:
            self.search_history = self.search_history[-max_history:]
        self._extract_entities(query)
        for result in results:
            self._extract_entities(result.get("title", ""))
            self._extract_entities(result.get("snippet", ""))

    def _extract_entities(self, text: str) -> None:
        from . import SPACY_AVAILABLE as pkg_SPACY_AVAILABLE

        if not pkg_SPACY_AVAILABLE or self.nlp is None:
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
        from . import (
            BERTOPIC_AVAILABLE as pkg_BERTOPIC_AVAILABLE,
            SENTENCE_TRANSFORMERS_AVAILABLE as pkg_SENTENCE_TRANSFORMERS_AVAILABLE,
        )

        if (
            not pkg_BERTOPIC_AVAILABLE
            or not self.search_history
            or not pkg_SENTENCE_TRANSFORMERS_AVAILABLE
        ):
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
        cfg = get_config()
        context_cfg = cfg.search.context_aware
        if not context_cfg.enabled:
            return query
        if self.topic_model is None or self.dictionary is None:
            self.build_topic_model()
        expanded_terms = sorted(self.entities, key=lambda e: self.entities[e], reverse=True)
        if expanded_terms:
            expansion_factor = context_cfg.expansion_factor
            num_terms = max(1, int(len(expanded_terms) * expansion_factor))
            selected_terms = expanded_terms[:num_terms]
            expanded_query = f"{query} {' '.join(selected_terms)}"
            log.info("Expanded query: '%s' -> '%s'", query, expanded_query)
            return expanded_query
        return query
