"""Search functionality for external information retrieval.

This subsystem is still experimental and only lightly tested. APIs and
behaviour may change in future revisions.

This module provides utilities for generating search queries and performing
external lookups using configurable search backends. It supports multiple
search backends, query generation, and result caching.

The module includes:
1. A Search class with methods for query generation and external lookups
2. Decorator for registering search backends
3. Built-in backends for DuckDuckGo and Serper
4. Error handling for network issues, timeouts, and invalid responses

See also the algorithm references in ``docs/algorithms`` for detailed
descriptions of the ranking components:

* ``docs/algorithms/bm25.md`` – lexical BM25 scoring
* ``docs/algorithms/semantic_similarity.md`` – embedding-based similarity
* ``docs/algorithms/source_credibility.md`` – domain credibility heuristics
* ``docs/algorithms/relevance_ranking.md`` – convergence of the combined score
"""

from __future__ import annotations

import ast
import csv
import importlib
import functools
import json
import math
import os
import re
import shutil
import subprocess
import warnings
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Concatenate,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    ParamSpec,
    Protocol,
    Sequence,
    Tuple,
    TypedDict,
    TypeVar,
    cast,
)
from weakref import WeakSet

import numpy as np
import requests

from ..cache import (
    SearchCache,
)
from ..cache import cache_results as _cache_results
from ..cache import (
    get_cache,
)
from ..cache import get_cached_results as _get_cached_results
from ..config.loader import get_config
from ..errors import ConfigError, NotFoundError, SearchError, StorageError
from ..logging_utils import get_logger
from ..storage import StorageManager
from . import storage as search_storage
from .context import SearchContext
from .http import close_http_session, get_http_session

# Re-export parser helpers so downstream imports stay stable.
from .parsers import (  # noqa: F401
    ParserDependencyError,
    ParserError,
    extract_docx_text,
    extract_pdf_text,
    read_document_text,
)
from .ranking import combine_scores
from .ranking import normalize_scores as _normalize_scores

Repo: Any | None
try:
    from git import Repo as GitRepo  # noqa: E402

    Repo = GitRepo
    GITPYTHON_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Repo = None
    GITPYTHON_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi  # noqa: E402

    BM25_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    BM25_AVAILABLE = False

if not GITPYTHON_AVAILABLE:
    warnings.warn(
        "Local Git search backend disabled: 'gitpython' is not installed. "
        'Install with `pip install "autoresearch[git]"` to enable it.',
        stacklevel=2,
    )

# Re-export cache helpers for backward compatibility
cache_results = _cache_results
get_cached_results = _get_cached_results

SentenceTransformer: type[SentenceTransformerType] | None = None
SENTENCE_TRANSFORMERS_AVAILABLE = False


def _resolve_sentence_transformer_cls() -> type[SentenceTransformerType] | None:
    """Resolve the fastembed embedding class, preferring the new API."""
    candidates: tuple[tuple[str, str], ...] = (
        ("fastembed", "OnnxTextEmbedding"),
        ("fastembed.text", "OnnxTextEmbedding"),
        ("fastembed", "TextEmbedding"),
    )
    for module_name, attr in candidates:
        try:
            module = importlib.import_module(module_name)
            return cast(type[SentenceTransformerType], getattr(module, attr))
        except (ImportError, ModuleNotFoundError, AttributeError):
            continue
    return None


def _try_import_sentence_transformers() -> bool:
    """Import an embedding model from fastembed or sentence-transformers.

    Preference order:
    1) fastembed.OnnxTextEmbedding (or TextEmbedding)
    2) sentence_transformers.SentenceTransformer
    """
    global SentenceTransformer, SENTENCE_TRANSFORMERS_AVAILABLE
    if SentenceTransformer is not None or SENTENCE_TRANSFORMERS_AVAILABLE:
        return SENTENCE_TRANSFORMERS_AVAILABLE
    cfg = _get_runtime_config()
    if not (cfg.search.context_aware.enabled or cfg.search.use_semantic_similarity):
        return False
    try:  # pragma: no cover - optional dependency
        resolved = _resolve_sentence_transformer_cls()
        if resolved is None:
            # Fallback to sentence-transformers if available
            try:
                from sentence_transformers import SentenceTransformer as ST

                resolved = ST
            except Exception:
                resolved = None
        if resolved is None:
            raise ImportError("No embedding backend available (fastembed or sentence-transformers)")
        SentenceTransformer = resolved
        SENTENCE_TRANSFORMERS_AVAILABLE = True
    except Exception:
        SentenceTransformer = None
        SENTENCE_TRANSFORMERS_AVAILABLE = False
    return SENTENCE_TRANSFORMERS_AVAILABLE


if TYPE_CHECKING:  # pragma: no cover - for type checking only
    try:
        from fastembed import OnnxTextEmbedding as SentenceTransformerType
    except (ImportError, ModuleNotFoundError, AttributeError):
        try:
            from fastembed.text import OnnxTextEmbedding as SentenceTransformerType
        except (ImportError, ModuleNotFoundError, AttributeError):
            from fastembed import TextEmbedding as SentenceTransformerType
else:  # pragma: no cover - runtime fallback
    SentenceTransformerType = Any

log = get_logger(__name__)


class ContextAwareConfigProtocol(Protocol):
    """Protocol describing the context-aware search configuration subset."""

    enabled: bool
    use_topic_modeling: bool


class LocalFileConfigProtocol(Protocol):
    """Protocol describing the local file search configuration subset."""

    path: str
    file_types: Sequence[str]


class LocalGitConfigProtocol(Protocol):
    """Protocol describing the local Git search configuration subset."""

    repo_path: str
    branches: Sequence[str]
    history_depth: int


class SearchConfigProtocol(Protocol):
    """Protocol capturing search configuration attributes consumed here."""

    backends: Sequence[str]
    embedding_backends: Sequence[str]
    hybrid_query: bool
    use_semantic_similarity: bool
    use_bm25: bool
    use_source_credibility: bool
    bm25_weight: float
    semantic_similarity_weight: float
    source_credibility_weight: float
    max_workers: int
    context_aware: ContextAwareConfigProtocol
    local_file: LocalFileConfigProtocol
    local_git: LocalGitConfigProtocol


class ConfigProtocol(Protocol):
    """Protocol describing the configuration object required by search."""

    search: SearchConfigProtocol


def _coerce_bool(value: Any, default: bool) -> bool:
    """Return ``value`` as a boolean, falling back to ``default`` when unknown."""

    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
        return default
    if value is None:
        return default
    try:
        return bool(value)
    except Exception:  # pragma: no cover - defensive for odd fixtures
        return default


def _coerce_float(value: Any, default: float) -> float:
    """Convert ``value`` to ``float`` while tolerating fixture stubs."""

    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        log.debug("Falling back to default float for search config", exc_info=True)
        return default


def _coerce_int(value: Any, default: int, *, minimum: int = 0) -> int:
    """Convert ``value`` to ``int`` bounded below by ``minimum``."""

    if value is None:
        return max(default, minimum)
    try:
        coerced = int(value)
    except (TypeError, ValueError):
        log.debug("Falling back to default int for search config", exc_info=True)
        return max(default, minimum)
    return coerced if coerced >= minimum else max(default, minimum)


def _normalize_str_sequence(value: Any, *, default: Sequence[str] = ()) -> tuple[str, ...]:
    """Return a tuple of strings from ``value`` while handling loose fixtures."""

    if value is None:
        return tuple(default)
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        try:
            return tuple(str(item) for item in value)
        except Exception:  # pragma: no cover - defensive
            return tuple(default)
    try:
        return tuple(str(item) for item in list(value))
    except Exception:  # pragma: no cover - defensive
        return tuple(default)


@dataclass(frozen=True, slots=True)
class _ContextAwareConfig(ContextAwareConfigProtocol):
    """Typed view over context-aware settings resilient to loose fixtures."""

    enabled: bool
    use_topic_modeling: bool

    @classmethod
    def from_object(cls, obj: Any) -> "_ContextAwareConfig":
        return cls(
            enabled=_coerce_bool(getattr(obj, "enabled", None), default=False),
            use_topic_modeling=_coerce_bool(getattr(obj, "use_topic_modeling", None), default=True),
        )


@dataclass(frozen=True, slots=True)
class _LocalFileConfig(LocalFileConfigProtocol):
    """Typed view for local file search configuration."""

    path: str
    file_types: Sequence[str]

    @classmethod
    def from_object(cls, obj: Any) -> "_LocalFileConfig":
        return cls(
            path=str(getattr(obj, "path", "")),
            file_types=_normalize_str_sequence(getattr(obj, "file_types", None), default=("txt",)),
        )


@dataclass(frozen=True, slots=True)
class _LocalGitConfig(LocalGitConfigProtocol):
    """Typed view for local Git search configuration."""

    repo_path: str
    branches: Sequence[str]
    history_depth: int

    @classmethod
    def from_object(cls, obj: Any) -> "_LocalGitConfig":
        return cls(
            repo_path=str(getattr(obj, "repo_path", "")),
            branches=_normalize_str_sequence(getattr(obj, "branches", None), default=("main",)),
            history_depth=_coerce_int(getattr(obj, "history_depth", None), default=50, minimum=1),
        )


@dataclass(frozen=True, slots=True)
class _SearchConfig(SearchConfigProtocol):
    """Typed adapter ensuring ``Search`` sees a consistent configuration."""

    backends: Sequence[str]
    embedding_backends: Sequence[str]
    hybrid_query: bool
    use_semantic_similarity: bool
    use_bm25: bool
    use_source_credibility: bool
    bm25_weight: float
    semantic_similarity_weight: float
    source_credibility_weight: float
    max_workers: int
    context_aware: ContextAwareConfigProtocol
    local_file: LocalFileConfigProtocol
    local_git: LocalGitConfigProtocol

    @classmethod
    def from_object(cls, obj: Any) -> "_SearchConfig":
        backends = _normalize_str_sequence(getattr(obj, "backends", None))
        embedding_backends = _normalize_str_sequence(getattr(obj, "embedding_backends", None))
        context_obj = getattr(obj, "context_aware", SimpleNamespace())
        local_file_obj = getattr(obj, "local_file", SimpleNamespace())
        local_git_obj = getattr(obj, "local_git", SimpleNamespace())
        return cls(
            backends=backends,
            embedding_backends=embedding_backends,
            hybrid_query=_coerce_bool(getattr(obj, "hybrid_query", None), default=False),
            use_semantic_similarity=_coerce_bool(
                getattr(obj, "use_semantic_similarity", None), default=True
            ),
            use_bm25=_coerce_bool(getattr(obj, "use_bm25", None), default=True),
            use_source_credibility=_coerce_bool(
                getattr(obj, "use_source_credibility", None), default=True
            ),
            bm25_weight=_coerce_float(getattr(obj, "bm25_weight", None), default=0.3),
            semantic_similarity_weight=_coerce_float(
                getattr(obj, "semantic_similarity_weight", None), default=0.5
            ),
            source_credibility_weight=_coerce_float(
                getattr(obj, "source_credibility_weight", None), default=0.2
            ),
            max_workers=_coerce_int(
                getattr(obj, "max_workers", None),
                default=max(1, len(backends)) if backends else 4,
                minimum=1,
            ),
            context_aware=_ContextAwareConfig.from_object(context_obj),
            local_file=_LocalFileConfig.from_object(local_file_obj),
            local_git=_LocalGitConfig.from_object(local_git_obj),
        )


@dataclass(frozen=True, slots=True)
class _Config(ConfigProtocol):
    """Wrapper ensuring the core module always sees a typed search config."""

    search: SearchConfigProtocol

    @classmethod
    def from_object(cls, obj: Any) -> "_Config":
        search_obj = getattr(obj, "search", None)
        if search_obj is None:
            raise ConfigError(
                "Search configuration missing from runtime config",
                suggestion="Ensure 'search' is defined in the configuration file",
            )
        return cls(search=_SearchConfig.from_object(search_obj))


def _get_runtime_config() -> ConfigProtocol:
    """Return the active configuration cast to the search protocol."""

    return _Config.from_object(get_config())


@dataclass
class ExternalLookupResult:
    """Aggregate external lookup output with cache and storage handles."""

    query: str
    results: List[Dict[str, Any]]
    by_backend: Dict[str, List[Dict[str, Any]]]
    cache: SearchCache
    storage: type[StorageManager]

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self.results)

    def __len__(self) -> int:
        return len(self.results)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        return self.results[index]


class LocalGitResult(TypedDict, total=False):
    """Typed mapping describing entries produced by ``_local_git_backend``."""

    title: str
    url: str
    snippet: str
    commit: str
    author: str
    date: str
    diff: str


# Scores are bucketed on a 10^-6 grid before lexicographic tie-breaking. This scale
# balances reproducibility with fidelity: it is coarse enough to absorb floating
# point jitter while still distinguishing meaningful score deltas observed in
# ranking benchmarks.
RANKING_BUCKET_SCALE = 1_000_000


P = ParamSpec("P")
T_co = TypeVar("T_co")
R = TypeVar("R")


class hybridmethod(Generic[T_co, P, R]):
    """Descriptor allowing methods usable as instance or shared class methods."""

    def __init__(self, func: Callable[Concatenate[T_co, P], R]) -> None:
        self.func = func

    def __get__(
        self, obj: T_co | None, objtype: type[T_co] | None = None
    ) -> Callable[P, R]:
        if obj is None:
            if objtype is None or not hasattr(objtype, "get_instance"):
                raise AttributeError("hybridmethod requires a class with get_instance()")
            get_instance = cast(Callable[[], T_co], getattr(objtype, "get_instance"))

            @functools.wraps(self.func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                instance = get_instance()
                return self.func(instance, *args, **kwargs)

            return wrapper
        return cast(Callable[P, R], self.func.__get__(obj, objtype))


@dataclass(frozen=True)
class DomainAuthorityScore:
    """Immutable domain authority score used for credibility ranking."""

    domain: str
    score: float


DOMAIN_AUTHORITY_SCORES: Tuple[DomainAuthorityScore, ...] = (
    DomainAuthorityScore("wikipedia.org", 0.9),
    DomainAuthorityScore("github.com", 0.85),
    DomainAuthorityScore("stackoverflow.com", 0.8),
    DomainAuthorityScore("medium.com", 0.7),
    DomainAuthorityScore("arxiv.org", 0.85),
    DomainAuthorityScore("ieee.org", 0.9),
    DomainAuthorityScore("acm.org", 0.9),
    DomainAuthorityScore("nature.com", 0.95),
    DomainAuthorityScore("science.org", 0.95),
    DomainAuthorityScore("nih.gov", 0.95),
    DomainAuthorityScore("edu", 0.8),  # Educational domains
    DomainAuthorityScore("gov", 0.85),  # Government domains
)

# Precompute a mapping for fast lookup in credibility scoring
DOMAIN_AUTHORITY_MAP: Dict[str, float] = {da.domain: da.score for da in DOMAIN_AUTHORITY_SCORES}


class Search:
    """Provides utilities for search query generation and external lookups."""

    # Class-level registries for default backends
    _default_backends: ClassVar[Dict[str, Callable[[str, int], List[Dict[str, Any]]]]] = {}
    _builtin_backends: ClassVar[Dict[str, Callable[[str, int], List[Dict[str, Any]]]]] = {}
    _default_embedding_backends: ClassVar[
        Dict[str, Callable[[np.ndarray, int], List[Dict[str, Any]]]]
    ] = {}
    _builtin_embedding_backends: ClassVar[
        Dict[str, Callable[[np.ndarray, int], List[Dict[str, Any]]]]
    ] = {}
    # Expose shared instance registries for legacy access
    backends: Dict[str, Callable[[str, int], List[Dict[str, Any]]]] = _default_backends
    embedding_backends: Dict[str, Callable[[np.ndarray, int], List[Dict[str, Any]]]] = (
        _default_embedding_backends
    )
    _shared_instance: ClassVar[Optional["Search"]] = None
    _instances: ClassVar[WeakSet["Search"]] = WeakSet()

    def __init__(self, cache: Optional[SearchCache] = None) -> None:
        self.backends: Dict[str, Callable[[str, int], List[Dict[str, Any]]]] = dict(
            self._default_backends
        )
        self.embedding_backends: Dict[str, Callable[[np.ndarray, int], List[Dict[str, Any]]]] = (
            dict(self._default_embedding_backends)
        )
        self._sentence_transformer: Optional[SentenceTransformerType] = None
        self.cache: SearchCache = cache or get_cache()
        type(self)._instances.add(self)

    @classmethod
    def get_instance(cls) -> "Search":
        """Return the shared Search instance used by class-level calls."""
        if cls._shared_instance is None:
            cls._shared_instance = cls()
        cls.backends = cls._shared_instance.backends
        cls.embedding_backends = cls._shared_instance.embedding_backends
        return cls._shared_instance

    @staticmethod
    def get_http_session() -> requests.Session:
        """Expose pooled HTTP session."""
        return get_http_session()

    @staticmethod
    def close_http_session() -> None:
        """Close the pooled HTTP session."""
        close_http_session()

    @hybridmethod
    def reset(self) -> None:
        """Reset registries and close pooled resources."""
        # Restore class-level registries to their built-in state
        type(self)._default_backends = dict(self._builtin_backends)
        type(self)._default_embedding_backends = dict(self._builtin_embedding_backends)
        self.backends = dict(type(self)._default_backends)
        self.embedding_backends = dict(type(self)._default_embedding_backends)
        self._sentence_transformer = None
        type(self)._sentence_transformer = None
        self.close_http_session()
        type(self).backends = self.backends
        type(self).embedding_backends = self.embedding_backends

    @hybridmethod
    @contextmanager
    def temporary_state(self) -> Iterator["Search"]:
        """Yield a Search instance with isolated state."""
        temp = type(self)(cache=self.cache)
        temp.backends = dict(self.backends)
        temp.embedding_backends = dict(self.embedding_backends)
        try:
            yield temp
        finally:
            temp.close_http_session()

    @hybridmethod
    def get_sentence_transformer(self) -> Optional[SentenceTransformerType]:
        """Get or initialize the fastembed model."""
        if not _try_import_sentence_transformers():
            log.warning(
                "fastembed package is not installed. Semantic similarity scoring will be disabled.",
            )
            return None

        if self._sentence_transformer is None:
            try:
                assert SentenceTransformer is not None
                self._sentence_transformer = SentenceTransformer()
                log.info("Initialized fastembed model")
            except Exception as e:
                log.warning(f"Failed to initialize fastembed model: {e}")
                return None

        return self._sentence_transformer

    @staticmethod
    def _coerce_embedding(raw: Any) -> Optional[np.ndarray]:
        """Convert embedding outputs to a numpy array."""

        if raw is None:
            return None
        if isinstance(raw, np.ndarray):
            if raw.ndim == 1:
                return raw.astype(float)
            if raw.ndim >= 2:
                return np.array(raw[0], dtype=float)
        if isinstance(raw, (int, float)):
            return np.array([float(raw)], dtype=float)
        if isinstance(raw, (list, tuple)):
            if not raw:
                return None
            first = raw[0]
            if isinstance(first, (list, tuple, np.ndarray)):
                return np.array(first, dtype=float)
            if isinstance(first, (int, float)):
                return np.array(raw, dtype=float)
        if hasattr(raw, "__iter__") and not isinstance(raw, (str, bytes)):
            try:
                seq = list(raw)
            except TypeError:
                return None
            if not seq:
                return None
            first = seq[0]
            if isinstance(first, (list, tuple, np.ndarray)):
                return np.array(first, dtype=float)
            if isinstance(first, (int, float)):
                return np.array(seq, dtype=float)
            if hasattr(first, "__iter__") and not isinstance(first, (str, bytes)):
                try:
                    nested = list(first)
                except TypeError:
                    return None
                if nested:
                    return np.array(nested, dtype=float)
        return None

    @hybridmethod
    def compute_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """Return a numeric embedding for ``query`` when a model is available."""

        model = self.get_sentence_transformer()
        if model is None:
            return None

        if hasattr(model, "embed"):
            try:
                raw = model.embed([query])
            except TypeError:
                raw = model.embed(query)
            embedding = self._coerce_embedding(raw)
            if embedding is not None:
                return embedding

        if hasattr(model, "encode"):
            try:
                raw = model.encode([query])
            except TypeError:
                raw = model.encode(query)
            embedding = self._coerce_embedding(raw)
            if embedding is not None:
                return embedding

        return None

    @staticmethod
    def preprocess_text(text: str) -> List[str]:
        """Preprocess text for ranking algorithms.

        Args:
            text: The text to preprocess

        Returns:
            List[str]: The preprocessed tokens
        """
        # Convert to lowercase
        text = text.lower()

        # Remove special characters and numbers
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\d+", " ", text)

        # Split into tokens and remove empty tokens
        tokens = [token for token in text.split() if token]

        return tokens

    @staticmethod
    def calculate_bm25_scores(query: str, documents: List[Dict[str, str]]) -> List[float]:
        """Calculate BM25 scores for a query and documents.

        See ``docs/algorithms/bm25.md`` for the formula and normalization
        approach.

        Args:
            query: The search query
            documents: The documents to score

        Returns:
            List[float]: The BM25 scores for each document
        """
        if not BM25_AVAILABLE:
            log.warning("rank-bm25 package is not installed. BM25 scoring will be disabled.")
            return [1.0] * len(documents)  # Return neutral scores

        # Preprocess the query
        query_tokens = Search.preprocess_text(query)

        # Preprocess the documents
        corpus = []
        for doc in documents:
            # Combine title and snippet if available
            doc_text = doc.get("title", "")
            if "snippet" in doc:
                doc_text += " " + doc.get("snippet", "")
            corpus.append(Search.preprocess_text(doc_text))

        # If corpus is empty, return neutral scores
        if not corpus or not query_tokens:
            return [1.0] * len(documents)

        try:
            # Use patched scores when BM25Okapi is mocked in tests
            if getattr(BM25Okapi, "__module__", "") == "unittest.mock":
                bm25 = BM25Okapi.return_value
                scores = bm25.get_scores(query_tokens)
            else:
                bm25 = BM25Okapi(corpus)
                scores = bm25.get_scores(query_tokens)

            # Ensure numpy array for consistent numeric operations
            scores = np.asarray(scores, dtype=float)

            # Normalize scores to [0, 1] range
            if scores.size:
                min_score = float(scores.min())
                max_score = float(scores.max())
                if max_score > min_score:
                    scores = (scores - min_score) / (max_score - min_score)
                elif max_score > 0:
                    scores = scores / max_score
                else:
                    scores = np.ones_like(scores)
                scores = np.clip(scores, 0.0, 1.0)

            return cast(List[float], scores.tolist())
        except Exception as e:
            log.warning(f"BM25 scoring failed: {e}")
            return [1.0] * len(documents)  # Return neutral scores

    @hybridmethod
    def calculate_semantic_similarity(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[float]:
        """Calculate semantic similarity scores for a query and documents.

        See ``docs/algorithms/semantic_similarity.md`` for the cosine
        similarity formulation and normalization used.

        Args:
            query: The search query
            documents: The documents to score

        Returns:
            List[float]: The semantic similarity scores for each document
        """
        model = self.get_sentence_transformer()
        if model is None and query_embedding is None:
            return [0.5] * len(documents)  # Return neutral scores

        try:
            if query_embedding is None:
                # Encode the query
                assert model is not None
                query_embedding = np.array(list(model.embed([query]))[0], dtype=float)

            # Encode the documents
            similarities: List[Optional[float]] = []
            to_encode: List[str] = []
            encode_map: List[int] = []

            for idx, doc in enumerate(documents):
                if "similarity" in doc:
                    sim = float(doc["similarity"])
                    similarities.append((sim + 1) / 2)
                    continue
                if "embedding" in doc:
                    doc_embedding = np.array(doc["embedding"], dtype=float)
                    sim = np.dot(query_embedding, doc_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                    )
                    similarities.append((sim + 1) / 2)
                    continue

                # Fallback to encoding text
                doc_text = doc.get("title", "")
                if "snippet" in doc:
                    doc_text += " " + doc.get("snippet", "")
                to_encode.append(doc_text)
                encode_map.append(idx)
                similarities.append(None)

            if to_encode:
                assert model is not None
                doc_embeddings = list(model.embed(to_encode))
                for emb, index in zip(doc_embeddings, encode_map):
                    emb_arr = np.array(emb, dtype=float)
                    sim = np.dot(query_embedding, emb_arr) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(emb_arr)
                    )
                    similarities[index] = (sim + 1) / 2

            return [s if s is not None else 0.5 for s in similarities]
        except Exception as e:
            log.warning(f"Semantic similarity calculation failed: {e}")
            return [0.5] * len(documents)  # Return neutral scores

    @hybridmethod
    def add_embeddings(
        self,
        documents: List[Dict[str, Any]],
        query_embedding: Optional[np.ndarray] = None,
    ) -> None:
        """Add embeddings and similarity scores to documents in-place."""
        model = self.get_sentence_transformer()
        if model is None:
            return

        texts: List[str] = []
        indices: List[int] = []
        for idx, doc in enumerate(documents):
            if "embedding" in doc:
                continue
            text = doc.get("title", "")
            if "snippet" in doc:
                text += " " + doc.get("snippet", "")
            texts.append(text)
            indices.append(idx)

        if not texts:
            return

        try:
            doc_embeddings = list(model.embed(texts))
            for emb, index in zip(doc_embeddings, indices):
                if hasattr(emb, "tolist"):
                    documents[index]["embedding"] = emb.tolist()
                else:
                    documents[index]["embedding"] = list(emb)
                if query_embedding is not None:
                    q = np.array(query_embedding, dtype=float)
                    emb_arr = np.array(emb, dtype=float)
                    sim = float(np.dot(q, emb_arr) / (np.linalg.norm(q) * np.linalg.norm(emb_arr)))
                    documents[index]["similarity"] = (sim + 1) / 2
        except Exception as e:  # pragma: no cover - unexpected
            log.warning(f"Failed to add embeddings: {e}")

    @staticmethod
    def assess_source_credibility(documents: List[Dict[str, str]]) -> List[float]:
        """Assess the credibility of sources using domain authority heuristics.

        See ``docs/algorithms/source_credibility.md`` for the scoring
        background.

        Args:
            documents: The documents to assess

        Returns:
            List[float]: The credibility scores for each document
        """
        # This is a simplified implementation that could be enhanced with real domain authority data
        # and citation metrics in a production environment

        # Domain authority scores for common domains (simplified example)
        domain_authority = DOMAIN_AUTHORITY_MAP

        scores = []
        for doc in documents:
            url = doc.get("url", "")

            # Extract domain from URL
            domain = ""
            match = re.search(r"https?://(?:www\.)?([^/]+)", url)
            if match:
                domain = match.group(1)

            # Calculate base score from domain authority
            score = 0.5  # Default score for unknown domains

            # Check for exact domain matches
            if domain in domain_authority:
                score = domain_authority[domain]
            else:
                # Check for partial domain matches (e.g., .edu, .gov)
                for partial_domain, authority in domain_authority.items():
                    if domain.endswith(partial_domain):
                        score = authority
                        break

            scores.append(score)

        return scores

    @staticmethod
    def merge_rank_scores(
        bm25_scores: List[float],
        semantic_scores: List[float],
        bm25_weight: float,
        semantic_weight: float,
    ) -> List[float]:
        """Merge BM25 and semantic scores using provided weights.

        See ``docs/algorithms/bm25.md`` and
        ``docs/algorithms/semantic_similarity.md`` for score details.
        """

        merged: List[float] = []
        for bm25, semantic in zip(bm25_scores, semantic_scores):
            merged.append(bm25 * bm25_weight + semantic * semantic_weight)
        return merged

    @staticmethod
    def normalize_scores(scores: List[float]) -> List[float]:
        """Scale scores to the 0–1 range.

        Args:
            scores: Raw relevance scores.

        Returns:
            List[float]: Normalized scores bounded by 0 and 1.
        """

        return _normalize_scores(scores)

    @staticmethod
    def merge_semantic_scores(
        semantic: List[float], duckdb: List[float]
    ) -> Tuple[List[float], List[float]]:
        """Average normalized semantic and vector similarities.

        If the vector store supplies no useful scores the semantic component
        is returned unchanged to preserve relative ordering.

        Args:
            semantic: Raw cosine similarities from the transformer.
            duckdb: Pre-computed similarities from the vector store.

        Returns:
            Tuple[List[float], List[float]]: Merged semantic scores and the
            normalized DuckDB scores.
        """

        semantic_norm = Search.normalize_scores(semantic)
        duckdb_norm = Search.normalize_scores(duckdb)
        if not duckdb_norm or max(duckdb_norm) <= 0:
            if semantic and len(set(semantic)) == 1:
                return [semantic[0]] * len(semantic), duckdb_norm
            return semantic_norm, duckdb_norm
        merged = [(semantic_norm[i] + duckdb_norm[i]) / 2 for i in range(len(semantic_norm))]
        return merged, duckdb_norm

    @hybridmethod
    def rank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[Dict[str, Any]]:
        """Rank search results using configurable relevance algorithms.

        The final score is a weighted combination of BM25, semantic
        similarity, and source credibility scores. See
        ``docs/algorithms/bm25.md``, ``docs/algorithms/semantic_similarity.md``,
        and ``docs/algorithms/source_credibility.md`` for details. Convergence
        of the weighted ranking is discussed in
        ``docs/algorithms/relevance_ranking.md``. Component scores are
        normalized to the 0–1 range before weighting, and the merged scores are
        normalized again before sorting. Weights are automatically normalized
        and fall back to equal values when all provided weights are zero.
        Semantic and DuckDB similarities are averaged after normalization so
        hybrid and semantic rankings share a consistent scale. When semantic
        similarity is disabled the normalized DuckDB scores serve as the
        semantic component to preserve weighting.

        Args:
            query: The search query
            results: The search results to rank

        Returns:
            List[Dict[str, str]]: The ranked search results
        """
        if not results:
            return results

        cfg = _get_runtime_config()
        search_cfg = cfg.search

        weights = {
            "bm25_weight": search_cfg.bm25_weight,
            "semantic_similarity_weight": search_cfg.semantic_similarity_weight,
            "source_credibility_weight": search_cfg.source_credibility_weight,
        }
        if not search_cfg.use_bm25:
            weights["bm25_weight"] = 0.0
        if not search_cfg.use_source_credibility:
            weights["source_credibility_weight"] = 0.0

        if any(value < 0 for value in weights.values()):
            raise ConfigError(
                "Relevance ranking weights must be non-negative",
                weights=weights,
                suggestion="Set negative weights to zero or a positive value",
            )

        weights_sum = sum(weights.values())
        tolerance = 0.001
        positive_components = sum(1 for value in weights.values() if value > tolerance)
        if weights_sum > 0 and positive_components >= 2 and abs(weights_sum - 1.0) > tolerance:
            raise ConfigError(
                "Relevance ranking weights must sum to 1.0",
                weights=weights,
                total=weights_sum,
                suggestion="Adjust the ranking weights so they total 1.0",
            )
        if weights_sum <= 0:
            enabled = [
                search_cfg.use_bm25,
                True,
                search_cfg.use_source_credibility,
            ]
            enabled_count = sum(enabled)
            if enabled_count == 0:
                raise ConfigError(
                    "At least one ranking weight must be positive and enabled",
                    weights=weights,
                    suggestion="Enable a component or increase its weight",
                )
            normalized_weights: tuple[float, float, float] = (
                1.0 / enabled_count if search_cfg.use_bm25 else 0.0,
                1.0 / enabled_count,
                1.0 / enabled_count if search_cfg.use_source_credibility else 0.0,
            )
        else:
            normalized_weights = (
                weights["bm25_weight"] / weights_sum,
                weights["semantic_similarity_weight"] / weights_sum,
                weights["source_credibility_weight"] / weights_sum,
            )

        # Calculate scores using different algorithms
        if search_cfg.use_bm25 and BM25_AVAILABLE:
            bm25_raw = type(self).calculate_bm25_scores(query, results)
            bm25_scores = self.normalize_scores(bm25_raw)
        else:
            bm25_raw = [0.0] * len(results)
            bm25_scores = [1.0] * len(results)

        if search_cfg.use_source_credibility:
            credibility_scores = self.normalize_scores(self.assess_source_credibility(results))
        else:
            credibility_scores = [1.0] * len(results)

        duckdb_raw = [r.get("similarity", 0.0) for r in results]
        if search_cfg.use_semantic_similarity:
            semantic_raw = self.calculate_semantic_similarity(query, results, query_embedding)
            semantic_scores, duckdb_scores = self.merge_semantic_scores(semantic_raw, duckdb_raw)
        else:
            # When semantic similarity is disabled, fall back to DuckDB raw scores
            semantic_raw = duckdb_raw
            duckdb_scores = self.normalize_scores(duckdb_raw)
            semantic_scores = duckdb_scores

        # All components are normalized to the 0–1 range before weighting.

        # Combine weighted scores using the shared ranking utility
        final_scores = combine_scores(
            bm25_scores,
            semantic_scores,
            credibility_scores,
            normalized_weights,
        )

        # Add scores and their quantized buckets for debugging/transparency. Buckets make
        # the tie-break logic explicit to downstream consumers and to the property-based
        # regression tests that validate deterministic ranking.
        for i, result in enumerate(results):
            result["relevance_score"] = final_scores[i]
            result["bm25_score"] = bm25_scores[i]
            result["semantic_score"] = semantic_scores[i]
            result["duckdb_score"] = duckdb_scores[i]
            result["credibility_score"] = credibility_scores[i]
            # Include both normalized and raw tie-breaker components
            semantic_component = semantic_scores[i] if semantic_scores[i] > 0 else 0.25
            result["merged_score"] = (
                bm25_scores[i] * normalized_weights[0] + semantic_component * normalized_weights[1]
            )
            result["raw_merged_score"] = (
                bm25_raw[i] * normalized_weights[0] + semantic_raw[i] * normalized_weights[1]
            )

        def _quantize(value: float, scale: int = RANKING_BUCKET_SCALE) -> int:
            """Map a floating point score to an integer grid for stable ordering."""

            if not math.isfinite(value):
                if math.isinf(value):
                    return int(scale * 1_000_000 if value > 0 else -scale * 1_000_000)
                return 0
            return int(round(value * scale))

        for result in results:
            result["relevance_bucket"] = _quantize(float(result.get("relevance_score", 0.0)))
            result["raw_relevance_bucket"] = _quantize(float(result.get("raw_merged_score", 0.0)))

        def _tie_break_key(item: Tuple[int, Dict[str, Any]]) -> Tuple[Any, ...]:
            index, doc = item
            return (
                -int(doc.get("relevance_bucket", 0)),
                -int(doc.get("raw_relevance_bucket", 0)),
                str(doc.get("backend") or ""),
                str(doc.get("url") or ""),
                str(doc.get("title") or ""),
                index,
            )

        # Sort by quantized score buckets first, then by deterministic identifiers. Using
        # an ascending sort with negated score buckets preserves descending ranking while
        # keeping tie resolution independent of floating point jitter.
        ranked_results = [
            result
            for _, result in sorted(
                enumerate(results),
                key=_tie_break_key,
            )
        ]

        return ranked_results

    @hybridmethod
    def cross_backend_rank(
        self,
        query: str,
        backend_results: Dict[str, List[Dict[str, Any]]],
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[Dict[str, Any]]:
        """Rank combined results from multiple backends.

        The same ranking pipeline used for individual backends is applied in
        two stages: results from each backend are first scored independently,
        then the combined set is re-ranked to produce the final ordering.
        """

        cfg = _get_runtime_config()
        if (
            query_embedding is None
            and cfg.search.use_semantic_similarity
            and cfg.search.context_aware.enabled
        ):
            model = self.get_sentence_transformer()
            if model is not None and hasattr(model, "embed"):
                query_embedding = np.array(list(model.embed([query]))[0], dtype=float)

        all_ranked: List[Dict[str, Any]] = []
        for name, docs in backend_results.items():
            ranked = self.rank_results(query, docs, query_embedding)
            for doc in ranked:
                doc.setdefault("backend", name)
                all_ranked.append(doc)

        return cast(
            List[Dict[str, Any]],
            self.rank_results(query, all_ranked, query_embedding),
        )

    @hybridmethod
    def embedding_lookup(
        self, query_embedding: np.ndarray, max_results: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform embedding-based search using registered backends."""
        cfg = _get_runtime_config()
        results: Dict[str, List[Dict[str, Any]]] = {}

        for name in cfg.search.embedding_backends:
            backend = self.embedding_backends.get(name)
            if not backend:
                log.warning(f"Unknown embedding backend '{name}'")
                continue
            try:
                backend_results = backend(query_embedding, max_results)
                results[name] = backend_results
            except Exception as exc:  # pragma: no cover - backend failure
                log.warning(f"{name} embedding search failed: {exc}")

        return results

    @hybridmethod
    def storage_hybrid_lookup(
        self,
        query: str,
        query_embedding: Optional[np.ndarray],
        backend_results: Dict[str, List[Dict[str, Any]]],
        max_results: int,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Combine storage-backed lexical, semantic, and ontology lookups."""

        aggregated: Dict[str, Dict[str, Any]] = {}
        source_map: Dict[str, set[str]] = {}

        def _claim_id(value: Any) -> str:
            text = str(value or "")
            if text.startswith("urn:claim:"):
                return text.split("urn:claim:", 1)[1]
            return text

        def _ensure_snippet(doc: Dict[str, Any], claim_id: str) -> None:
            snippet = doc.get("snippet") or doc.get("content")
            if snippet:
                doc["snippet"] = str(snippet)
                return
            try:
                claim = StorageManager.get_claim(claim_id)
            except Exception:
                claim = None
            if claim:
                content = claim.get("content")
                if content:
                    doc["snippet"] = str(content)
                if not doc.get("title") and content:
                    doc["title"] = str(content)[:60]

        def _normalise_embedding(embedding: Any) -> Optional[List[float]]:
            if embedding is None:
                return None
            if isinstance(embedding, np.ndarray):
                return embedding.astype(float).tolist()
            if hasattr(embedding, "tolist"):
                try:
                    return list(embedding.tolist())
                except Exception:  # pragma: no cover - defensive
                    return None
            if isinstance(embedding, (list, tuple)):
                try:
                    return [float(v) for v in embedding]
                except Exception:
                    return None
            return None

        def _ingest(doc: Dict[str, Any], source: str) -> None:
            claim_id = _claim_id(doc.get("url") or doc.get("node_id") or doc.get("id"))
            if not claim_id:
                return
            entry = aggregated.setdefault(claim_id, {"url": claim_id})
            title = doc.get("title") or doc.get("name")
            if title and not entry.get("title"):
                entry["title"] = str(title)
            snippet = doc.get("snippet") or doc.get("content")
            if snippet and not entry.get("snippet"):
                entry["snippet"] = str(snippet)
            _ensure_snippet(entry, claim_id)
            embedding = _normalise_embedding(doc.get("embedding"))
            if embedding is not None:
                entry["embedding"] = embedding
            similarity = doc.get("similarity")
            if similarity is not None:
                try:
                    entry["similarity"] = float(similarity)
                except (TypeError, ValueError):
                    pass
            if doc.get("ontology_matches"):
                matches = entry.setdefault("ontology_matches", [])
                for match in doc["ontology_matches"]:
                    predicate = str(match.get("predicate", ""))
                    value = str(match.get("value", ""))
                    matches.append({"predicate": predicate, "value": value})
            source_map.setdefault(claim_id, set()).add(source)

        vector_docs = list(backend_results.get("duckdb", []))
        if not vector_docs and query_embedding is not None:
            try:
                vector_hits = StorageManager.vector_search(query_embedding.tolist(), k=max_results)
            except (StorageError, NotFoundError, Exception) as exc:
                log.debug("Storage vector search unavailable: %s", exc)
                vector_hits = []
            for hit in vector_hits:
                claim_id = _claim_id(hit.get("node_id") or hit.get("id"))
                if not claim_id:
                    continue
                doc = {
                    "url": claim_id,
                    "title": hit.get("title") or hit.get("name"),
                    "snippet": hit.get("content") or hit.get("snippet"),
                    "embedding": hit.get("embedding"),
                    "similarity": hit.get("similarity"),
                }
                _ensure_snippet(doc, claim_id)
                vector_docs.append(doc)
        for doc in vector_docs:
            _ensure_snippet(doc, _claim_id(doc.get("url") or doc.get("node_id")))
            _ingest(doc, "vector")

        try:
            graph = StorageManager.get_graph()
        except NotFoundError:
            graph = None
        except Exception as exc:  # pragma: no cover - defensive
            log.debug("Graph unavailable for storage lookup: %s", exc)
            graph = None
        if graph is not None:
            sorted_nodes = sorted(graph.nodes(data=True), key=lambda item: str(item[0]))
            limit = max(max_results * 5, max_results)
            for node_id, data in sorted_nodes[:limit]:
                content = data.get("content") or data.get("text") or data.get("snippet")
                if not content:
                    continue
                doc = {
                    "url": _claim_id(node_id),
                    "title": data.get("title") or data.get("name"),
                    "snippet": content,
                }
                _ingest(doc, "bm25")

        tokens = self.preprocess_text(query)
        if tokens:
            filters = " || ".join(f'CONTAINS(LCASE(STR(?o)), "{token}")' for token in tokens)
            sparql = "SELECT ?s ?p ?o WHERE { ?s ?p ?o . FILTER(" + filters + ") }"
            try:
                rows = StorageManager.query_rdf(sparql)
            except (NotFoundError, StorageError, Exception) as exc:
                log.debug("Ontology lookup skipped: %s", exc)
            else:
                matches: List[Tuple[str, str, str]] = []
                for row in rows:
                    try:
                        subj = getattr(row, "s", row[0])
                        pred = getattr(row, "p", row[1])
                        obj = getattr(row, "o", row[2])
                    except Exception:  # pragma: no cover - rdflib row interface
                        continue
                    claim_id = _claim_id(subj)
                    value = str(obj)
                    matches.append((claim_id, str(pred), value))
                matches.sort()
                for claim_id, predicate, value in matches[: max_results * 2]:
                    doc = {
                        "url": claim_id,
                        "snippet": value,
                        "ontology_matches": [{"predicate": predicate, "value": value}],
                    }
                    _ingest(doc, "ontology")

        if not aggregated:
            return {}

        ordered: List[Dict[str, Any]] = []
        for claim_id in sorted(aggregated):
            entry = aggregated[claim_id]
            if "ontology_matches" in entry:
                matches = entry["ontology_matches"]
                entry["ontology_matches"] = sorted(
                    matches,
                    key=lambda item: (item.get("predicate", ""), item.get("value", "")),
                )
            sources = sorted(source_map.get(claim_id, set()))
            if sources:
                entry["storage_sources"] = sources
            entry.setdefault("title", claim_id)
            entry.setdefault("snippet", "")
            ordered.append(dict(entry))

        if query_embedding is not None:
            self.add_embeddings(ordered, query_embedding)

        return {"storage": ordered[: max_results * 3]}

    @staticmethod
    def load_evaluation_data(path: Path) -> Dict[str, List[Dict[str, float]]]:
        """Load ranking evaluation data from a CSV file."""

        data: Dict[str, List[Dict[str, float]]] = {}
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.setdefault(row["query"], []).append(
                    {
                        "bm25": float(row["bm25"]),
                        "semantic": float(row["semantic"]),
                        "credibility": float(row["credibility"]),
                        "relevance": float(row["relevance"]),
                    }
                )
        return data

    @staticmethod
    def _ndcg(relevances: List[float]) -> float:
        """Compute normalized discounted cumulative gain."""

        dcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(relevances))
        ideal = sorted(relevances, reverse=True)
        idcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
        return dcg / idcg if idcg else 0.0

    @classmethod
    def evaluate_weights(
        cls,
        weights: Tuple[float, float, float],
        data: Dict[str, List[Dict[str, float]]],
    ) -> float:
        """Evaluate ranking quality for the given weights using NDCG."""

        w_sem, w_bm, w_cred = weights
        total = 0.0
        for docs in data.values():
            scores = [
                w_sem * d["semantic"] + w_bm * d["bm25"] + w_cred * d["credibility"] for d in docs
            ]
            ranked = [
                docs[i]["relevance"]
                for i in sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)
            ]
            total += cls._ndcg(ranked)
        return total / len(data)

    @classmethod
    def tune_weights(
        cls, data: Dict[str, List[Dict[str, float]]], step: float = 0.1
    ) -> Tuple[float, float, float]:
        """Search for relevance weights that maximize NDCG."""

        best = (0.5, 0.3, 0.2)
        best_score = cls.evaluate_weights(best, data)
        steps = tuple(i * step for i in range(int(1 / step) + 1))
        for w_sem in steps:
            for w_bm in steps:
                w_cred = 1.0 - w_sem - w_bm
                if w_cred < 0 or w_cred > 1:
                    continue
                score = cls.evaluate_weights((w_sem, w_bm, w_cred), data)
                if score > best_score:
                    best_score = score
                    best = (w_sem, w_bm, w_cred)
        return best

    @classmethod
    def optimize_weights(
        cls, data: Dict[str, List[Dict[str, float]]], step: float = 0.1
    ) -> Tuple[Tuple[float, float, float], float]:
        """Return the best weights and corresponding NDCG score."""

        best = cls.tune_weights(data, step=step)
        score = cls.evaluate_weights(best, data)
        return best, score

    @classmethod
    def register_backend(cls, name: str) -> Callable[
        [Callable[[str, int], List[Dict[str, Any]]]],
        Callable[[str, int], List[Dict[str, Any]]],
    ]:
        """Register a search backend function.

        This decorator registers a function as a search backend with the given name.
        Registered backends can be used by configuring them in the search_backends
        list in the configuration.

        Args:
            name: The name to register the backend under. This name should be used
                  in the configuration to enable the backend.

        Returns:
            A decorator function that registers the decorated function as a search
            backend and returns the original function unchanged.

        Example:
            @Search.register_backend("custom")
            def custom_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
                # Implementation
                return [{"title": "Result", "url": "https://example.com"}]
        """

        def decorator(
            func: Callable[[str, int], List[Dict[str, Any]]],
        ) -> Callable[[str, int], List[Dict[str, Any]]]:
            cls._default_backends[name] = func
            if cls._shared_instance is not None:
                cls._shared_instance.backends[name] = func
                cls.backends = cls._shared_instance.backends
            else:
                cls._builtin_backends[name] = func
            for inst in cls._instances:
                inst.backends[name] = func
            return func

        return decorator

    @classmethod
    def register_embedding_backend(cls, name: str) -> Callable[
        [Callable[[np.ndarray, int], List[Dict[str, Any]]]],
        Callable[[np.ndarray, int], List[Dict[str, Any]]],
    ]:
        """Register an embedding search backend."""

        def decorator(
            func: Callable[[np.ndarray, int], List[Dict[str, Any]]],
        ) -> Callable[[np.ndarray, int], List[Dict[str, Any]]]:
            cls._default_embedding_backends[name] = func
            if cls._shared_instance is not None:
                cls._shared_instance.embedding_backends[name] = func
                cls.embedding_backends = cls._shared_instance.embedding_backends
            else:
                cls._builtin_embedding_backends[name] = func
            for inst in cls._instances:
                inst.embedding_backends[name] = func
            return func

        return decorator

    @staticmethod
    def generate_queries(query: str, return_embeddings: bool = False) -> List[Any]:
        """Generate search query variants or a simple embedding for a query.

        This method takes a raw user query and either generates multiple variants
        of the query to improve search results, or creates a simple vector embedding
        of the query for vector search.

        The query variants include:
        1. The original query
        2. The query with "examples" appended (if query has multiple words)
        3. The query in question form ("What is X?")

        When return_embeddings is True, a simple deterministic embedding is created
        using character codes. This is primarily used for testing and demonstration
        purposes.

        Args:
            query: The raw user query string to generate variants or embeddings for.
            return_embeddings: When True, return a numeric embedding instead of
                              query strings. Default is False.

        Returns:
            A list of query variants (strings) or a list of floating-point values
            representing a simple embedding of the query.

        Example:
            >>> Search.generate_queries("python")
            ['python', 'python examples', 'What is python?']

            >>> Search.generate_queries("a", return_embeddings=True)
            [97.0]
        """

        cleaned = query.strip()

        if return_embeddings:
            # Create a trivial embedding using character codes. This keeps the
            # implementation lightweight and deterministic for unit tests.
            return [float(ord(c)) for c in cleaned][:10]

        queries = [cleaned]

        # Add a simple variation emphasising examples or tutorials
        if len(cleaned.split()) > 1:
            queries.append(f"{cleaned} examples")

        # Include a question style variant
        queries.append(f"What is {cleaned}?")

        return queries

    @hybridmethod
    def external_lookup(
        self,
        query: str | Dict[str, Any],
        max_results: int = 5,
        *,
        return_handles: bool = False,
    ) -> List[Dict[str, Any]] | ExternalLookupResult:
        """Perform an external search using configured backends.

        This method performs a search using all backends configured in the
        search_backends list in the configuration. It handles caching of results,
        error handling, and merging results from multiple backends.

        The method attempts to use each configured backend in sequence. If a backend
        fails, it logs the error and continues with the next backend. If all backends
        fail, it returns fallback results.

        If context-aware search is enabled, this method will:
        1. Expand the query based on search context (entities, topics, history)
        2. Update the search context with the new query and results
        3. Build or update the topic model if needed

        Args:
            query: The search query string to look up.
            max_results: The maximum number of results to return per backend.
                Default is 5.
            return_handles: When ``True`` return an
                :class:`ExternalLookupResult` bundling the ranked results,
                cache handle, and storage manager reference. Defaults to
                ``False`` for backwards compatibility.

        Returns:
            A list of dictionaries containing search results. Each dictionary
            has at least 'title' and 'url' keys. When ``return_handles`` is
            ``True`` an :class:`ExternalLookupResult` is returned instead,
            providing the ranked results alongside the storage and cache
            handles used to hydrate them.

        Raises:
            SearchError: If a search backend fails due to network issues, invalid
                        JSON responses, or other errors.
            TimeoutError: If a search backend times out.

        Example:
            >>> Search.external_lookup("python", max_results=2)
            [
                {"title": "Python Programming Language", "url": "https://python.org"},
                {"title": "Python (programming language) - Wikipedia", "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"}
            ]
        """
        cfg = _get_runtime_config()

        if isinstance(query, dict):
            text_query = str(query.get("text", ""))
            query_embedding = query.get("embedding")
        else:
            text_query = query
            query_embedding = None

        # Apply context-aware search if enabled
        context_cfg = cfg.search.context_aware
        if context_cfg.enabled:
            # Get the search context
            context = SearchContext.get_instance()

            # Expand the query based on context
            expanded_query = context.expand_query(text_query)

            # Use the expanded query if available
            if expanded_query != text_query:
                log.info(f"Using context-aware expanded query: '{expanded_query}'")
                search_query = expanded_query
            else:
                search_query = text_query
        else:
            search_query = text_query

        results: List[Dict[str, Any]] = []
        results_by_backend: Dict[str, List[Dict[str, Any]]] = {}

        np_query_embedding: Optional[np.ndarray] = None
        if query_embedding is not None:
            try:
                np_query_embedding = np.array(query_embedding, dtype=float)
            except Exception:  # pragma: no cover - defensive
                np_query_embedding = None
        else:
            need_embedding = (
                cfg.search.hybrid_query
                or cfg.search.use_semantic_similarity
                or bool(cfg.search.embedding_backends)
            )
            if not need_embedding:
                try:
                    need_embedding = StorageManager.has_vss()
                except Exception:  # pragma: no cover - optional dependency
                    need_embedding = False
            if need_embedding:
                np_query_embedding = self.compute_query_embedding(search_query)

        if np_query_embedding is not None:
            emb_results = self.embedding_lookup(np_query_embedding, max_results)
            for name, docs in emb_results.items():
                results_by_backend[name] = docs
                results.extend(docs)

        def run_backend(name: str) -> Tuple[str, List[Dict[str, Any]]]:
            backend = self.backends.get(name)
            if not backend:
                log.warning(f"Unknown search backend '{name}'")
                available_backends = list(self.backends.keys()) or ["No backends registered"]
                raise SearchError(
                    f"Unknown search backend '{name}'",
                    available_backends=available_backends,
                    provided=name,
                    suggestion="Configure a valid search backend in your configuration file",
                )

            cached = self.cache.get_cached_results(search_query, name)
            if cached is not None:
                self.add_embeddings(cached, np_query_embedding)
                for r in cached:
                    r.setdefault("backend", name)
                return name, cached[:max_results]

            try:
                backend_results = backend(search_query, max_results)
            except requests.exceptions.Timeout as exc:
                log.warning(f"{name} search timed out: {exc}")
                from ..errors import TimeoutError

                raise TimeoutError(
                    f"{name} search timed out",
                    cause=exc,
                    backend=name,
                    query=text_query,
                )
            except requests.exceptions.RequestException as exc:
                log.warning(f"{name} search request failed: {exc}")
                raise SearchError(
                    f"{name} search failed",
                    cause=exc,
                    backend=name,
                    query=text_query,
                    suggestion="Check your network connection and ensure the search backend is properly configured",
                )
            except json.JSONDecodeError as exc:
                log.warning(f"{name} search returned invalid JSON: {exc}")
                raise SearchError(
                    f"{name} search failed: invalid JSON response",
                    cause=exc,
                    backend=name,
                    query=text_query,
                    suggestion="The search backend returned an invalid response. Try a different search query or backend.",
                )
            except Exception as exc:  # pragma: no cover - unexpected errors
                log.warning(f"{name} search failed with unexpected error: {exc}")
                raise SearchError(
                    f"{name} search failed",
                    cause=exc,
                    backend=name,
                    query=text_query,
                    suggestion="An unexpected error occurred. Check the logs for more details and consider using a different search backend.",
                )

            if backend_results:
                for r in backend_results:
                    r.setdefault("backend", name)
            self.cache.cache_results(search_query, name, backend_results)
            self.add_embeddings(backend_results, np_query_embedding)
            return name, backend_results

        max_workers = getattr(cfg.search, "max_workers", len(cfg.search.backends))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures: Dict[Future[Tuple[str, List[Dict[str, Any]]]], str] = {
                executor.submit(run_backend, name): name for name in cfg.search.backends
            }
            for future in as_completed(futures):
                name, backend_results = future.result()
                if backend_results:
                    results_by_backend[name] = backend_results
                    results.extend(backend_results)

        storage_results = self.storage_hybrid_lookup(
            text_query, np_query_embedding, results_by_backend, max_results
        )
        for name, docs in storage_results.items():
            if not docs:
                continue
            if name in results_by_backend:
                results_by_backend[name].extend(docs)
            else:
                results_by_backend[name] = docs
        if storage_results.get("storage"):
            results_by_backend.pop("duckdb", None)
        results = []
        for docs in results_by_backend.values():
            results.extend(docs)

        if results:
            # Rank the results from all backends together
            ranked_results = self.cross_backend_rank(
                text_query, results_by_backend, np_query_embedding
            )

            search_storage.persist_results(ranked_results)

            # Update search context if context-aware search is enabled
            if cfg.search.context_aware.enabled:
                context = SearchContext.get_instance()

                # Add the query and results to the search history
                context.add_to_history(text_query, ranked_results)

                # Build or update the topic model if topic modeling is enabled
                if cfg.search.context_aware.use_topic_modeling:
                    context.build_topic_model()

            bundle = ExternalLookupResult(
                query=text_query,
                results=[dict(result) for result in ranked_results],
                by_backend={
                    name: [dict(doc) for doc in docs] for name, docs in results_by_backend.items()
                },
                cache=self.cache,
                storage=StorageManager,
            )
            return bundle if return_handles else bundle.results

        # Fallback results when all backends fail
        fallback_results = [
            {"title": f"Result {i + 1} for {text_query}", "url": ""} for i in range(max_results)
        ]
        bundle = ExternalLookupResult(
            query=text_query,
            results=[dict(result) for result in fallback_results],
            by_backend={
                name: [dict(doc) for doc in docs] for name, docs in results_by_backend.items()
            },
            cache=self.cache,
            storage=StorageManager,
        )

        return bundle if return_handles else bundle.results


def get_search() -> Search:
    """Return the shared :class:`Search` instance."""
    return Search.get_instance()


@Search.register_backend("duckduckgo")
def _duckduckgo_backend(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Retrieve search results from the DuckDuckGo API.

    This function queries the DuckDuckGo API with the given search query
    and returns the results in a standardized format. It extracts information
    from the RelatedTopics field in the API response.

    Args:
        query: The search query string to look up.
        max_results: The maximum number of results to return. Default is 5.

    Returns:
        A list of dictionaries containing search results. Each dictionary
        has 'title' and 'url' keys.

    Raises:
        requests.exceptions.Timeout: If the request to the DuckDuckGo API times out.
        requests.exceptions.RequestException: If there's a network error or the API
                                             returns an error status code.
        json.JSONDecodeError: If the API returns a response that can't be parsed as JSON.

    Note:
        This function is registered as a search backend with the name "duckduckgo"
        and can be enabled by adding "duckduckgo" to the search_backends list in
        the configuration.
    """
    url = "https://api.duckduckgo.com/"
    params: Dict[str, str] = {
        "q": query,
        "format": "json",
        "no_redirect": "1",
        "no_html": "1",
    }
    session = get_http_session()
    response = session.get(url, params=params, timeout=5)
    # Raise an exception for HTTP errors (4xx and 5xx)
    response.raise_for_status()
    data = response.json()
    results: List[Dict[str, str]] = []
    for item in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(item, dict):
            results.append(
                {
                    "title": item.get("Text", ""),
                    "url": item.get("FirstURL", ""),
                }
            )
    return results


@Search.register_backend("serper")
def _serper_backend(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Retrieve search results from the Serper API.

    This function queries the Serper API (a Google Search API) with the given
    search query and returns the results in a standardized format. It extracts
    information from the 'organic' field in the API response.

    Args:
        query: The search query string to look up.
        max_results: The maximum number of results to return. Default is 5.

    Returns:
        A list of dictionaries containing search results. Each dictionary
        has 'title' and 'url' keys.

    Raises:
        requests.exceptions.Timeout: If the request to the Serper API times out.
        requests.exceptions.RequestException: If there's a network error or the API
                                             returns an error status code.
        json.JSONDecodeError: If the API returns a response that can't be parsed as JSON.

    Note:
        This function is registered as a search backend with the name "serper"
        and can be enabled by adding "serper" to the search_backends list in
        the configuration. It requires a Serper API key to be set in the
        SERPER_API_KEY environment variable.
    """
    api_key = os.getenv("SERPER_API_KEY", "")
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key}
    session = get_http_session()
    response = session.post(url, json={"q": query}, headers=headers, timeout=5)
    # Raise an exception for HTTP errors (4xx and 5xx)
    response.raise_for_status()
    data = response.json()
    results: List[Dict[str, str]] = []
    for item in data.get("organic", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
            }
        )
    return results


@Search.register_backend("brave")
def _brave_backend(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Retrieve search results from the Brave Search API.

    This function queries the Brave Search API with the given search query
    and returns the results in a standardized format. It extracts information
    from the 'web' field in the API response.

    Args:
        query: The search query string to look up.
        max_results: The maximum number of results to return. Default is 5.

    Returns:
        A list of dictionaries containing search results. Each dictionary
        has 'title' and 'url' keys.

    Raises:
        requests.exceptions.Timeout: If the request to the Brave Search API times out.
        requests.exceptions.RequestException: If there's a network error or the API
                                             returns an error status code.
        json.JSONDecodeError: If the API returns a response that can't be parsed as JSON.

    Note:
        This function is registered as a search backend with the name "brave"
        and can be enabled by adding "brave" to the search_backends list in
        the configuration. It requires a Brave Search API key to be set in the
        BRAVE_SEARCH_API_KEY environment variable.
    """
    api_key = os.getenv("BRAVE_SEARCH_API_KEY", "")
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params: Dict[str, str | int] = {"q": query, "count": max_results}

    session = get_http_session()
    response = session.get(url, params=params, headers=headers, timeout=5)
    # Raise an exception for HTTP errors (4xx and 5xx)
    response.raise_for_status()
    data = response.json()
    results: List[Dict[str, str]] = []
    for item in data.get("web", {}).get("results", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
            }
        )
    return results


@Search.register_backend("local_file")
def _local_file_backend(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search plain text files on disk for a query."""

    cfg = _get_runtime_config()
    path = cfg.search.local_file.path
    file_types = cfg.search.local_file.file_types

    if not path:
        log.warning("local_file backend path not configured")
        return []

    root = Path(path)
    if not root.exists():
        log.warning("local_file path does not exist: %s", path)
        return []

    results: List[Dict[str, str]] = []

    rg_path = shutil.which("rg")
    text_exts = [ext for ext in file_types if ext not in {"pdf", "docx", "doc"}]
    doc_exts = [ext for ext in file_types if ext in {"pdf", "docx", "doc"}]

    if rg_path and text_exts:
        for ext in text_exts:
            if len(results) >= max_results:
                break
            cmd = [
                rg_path,
                "-n",
                "--no-heading",
                "-i",
                f"-m{max_results - len(results)}",
                "-g",
                f"*.{ext}",
                query,
                str(root),
            ]
            try:
                output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as exc:  # pragma: no cover - ripgrep no match
                output = exc.output or ""
            for line in output.splitlines():
                parts = line.split(":", 2)
                if len(parts) < 3:
                    continue
                file_path, _line_no, snippet = parts
                results.append(
                    {
                        "title": Path(file_path).name,
                        "url": file_path,
                        "snippet": snippet.strip(),
                    }
                )
                if len(results) >= max_results:
                    break

    patterns = [f"**/*.{ext}" for ext in doc_exts] if doc_exts else []
    patterns += [f"**/*.{ext}" for ext in text_exts] if not rg_path else []
    for pattern in patterns:
        for file in root.rglob(pattern):
            if not file.is_file():
                continue
            try:
                text = read_document_text(file)
            except ParserDependencyError as exc:
                log.warning("Parser dependency missing for %s: %s", file, exc)
                continue
            except ParserError as exc:
                log.info("Skipping unreadable document %s: %s", file, exc)
                continue
            except Exception as exc:  # pragma: no cover - unexpected file errors
                log.warning("Failed to read %s: %s", file, exc)
                continue

            idx = text.lower().find(query.lower())
            if idx != -1:
                snippet = text[idx : idx + 200]
                results.append({"title": file.name, "url": str(file), "snippet": snippet})
                if len(results) >= max_results:
                    return results

    return results


@Search.register_backend("local_git")
def _local_git_backend(query: str, max_results: int = 5) -> List[LocalGitResult]:
    """Search a local Git repository's files and commit messages."""

    cfg = _get_runtime_config()
    repo_path = cfg.search.local_git.repo_path
    branches = cfg.search.local_git.branches
    depth = cfg.search.local_git.history_depth

    if not repo_path:
        log.warning("local_git backend repo_path not configured")
        return []

    repo_root = Path(repo_path)
    if not repo_root.exists():
        log.warning("local_git repo_path does not exist: %s", repo_path)
        return []

    if Repo is None:
        raise SearchError("local_git backend requires gitpython")

    repo = Repo(repo_path)
    head_hash = repo.head.commit.hexsha

    results: List[LocalGitResult] = []

    # Search working tree files using ripgrep/Python scanning
    rg_path = shutil.which("rg")
    file_types = cfg.search.local_file.file_types
    if rg_path:
        for ext in file_types:
            if len(results) >= max_results:
                break
            cmd = [
                rg_path,
                "-n",
                "--no-heading",
                "-i",
                f"-m{max_results - len(results)}",
                "-g",
                f"*.{ext}",
                query,
                str(repo_root),
            ]
            try:
                output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as exc:  # pragma: no cover - ripgrep no match
                output = exc.output or ""
            for line in output.splitlines():
                parts = line.split(":", 2)
                if len(parts) < 3:
                    continue
                file_path, line_no_str, _snippet = parts
                try:
                    line_no = int(line_no_str)
                except ValueError:
                    line_no = 0
                context_lines = []
                try:
                    file_lines = Path(file_path).read_text(errors="ignore").splitlines()
                    start = max(0, line_no - 3)
                    end = min(len(file_lines), line_no + 2)
                    context_lines = file_lines[start:end]
                except Exception:
                    context_lines = [_snippet.strip()]
                snippet = "\n".join(context_lines)
                results.append(
                    {
                        "title": Path(file_path).name,
                        "url": file_path,
                        "snippet": snippet,
                        "commit": head_hash,
                    }
                )
                if len(results) >= max_results:
                    break
    else:
        for file in repo_root.rglob("*"):
            if not file.is_file():
                continue
            try:
                lines = file.read_text(errors="ignore").splitlines()
            except Exception:  # pragma: no cover - unexpected
                continue
            for idx, line in enumerate(lines):
                if query.lower() in line.lower():
                    start = max(0, idx - 2)
                    end = min(len(lines), idx + 3)
                    snippet = "\n".join(lines[start:end])
                    results.append(
                        {
                            "title": file.name,
                            "url": str(file),
                            "snippet": snippet,
                            "commit": head_hash,
                        }
                    )
                    break
            if len(results) >= max_results:
                return results

    # AST-based search for Python code structure
    normalized_query = query.lower().replace("_", "")
    for py_file in repo_root.rglob("*.py"):
        if len(results) >= max_results:
            break
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:  # pragma: no cover - parse errors
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name_norm = node.name.lower().replace("_", "")
                if normalized_query in name_norm:
                    start_line = getattr(node, "lineno", 1) - 1
                    end_line = getattr(node, "end_lineno", start_line + 1)
                    lines = source.splitlines()
                    snippet = "\n".join(lines[start_line:end_line])
                    results.append(
                        {
                            "title": py_file.name,
                            "url": str(py_file),
                            "snippet": snippet,
                            "commit": head_hash,
                        }
                    )
                    break
    if len(results) >= max_results:
        return results

    indexed: set[str] = set()
    # Persist a lightweight git index when storage is available. If storage
    # is unavailable (e.g., RDF backend missing in minimal test envs), skip
    # persistence gracefully to avoid coupling local git search to storage.
    try:
        with StorageManager.connection() as conn:
            try:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS git_index("
                    "commit_hash VARCHAR PRIMARY KEY, author VARCHAR, date TIMESTAMP, message VARCHAR, diff VARCHAR)"
                )
                rows = conn.execute("SELECT commit_hash FROM git_index").fetchall()
                indexed = {r[0] for r in rows}
            except Exception as exc:  # pragma: no cover - db errors
                log.warning(f"Failed to prepare git_index table: {exc}")

            for commit in repo.iter_commits(cast(Any, branches or None), max_count=depth):
                commit_hash = commit.hexsha
                diff_text = ""
                try:
                    parent = commit.parents[0] if commit.parents else None
                    diffs = commit.diff(parent, create_patch=True)
                    for d in diffs:
                        raw_diff = d.diff
                        if isinstance(raw_diff, bytes):
                            part = raw_diff.decode("utf-8", "ignore")
                        else:
                            part = str(raw_diff)
                        diff_text += part
                        if query.lower() in part.lower():
                            snippet_match = re.search(
                                rf".{{0,80}}{re.escape(query)}.{{0,80}}",
                                part,
                                re.IGNORECASE,
                            )
                            snippet = (
                                snippet_match.group(0).strip() if snippet_match else part[:200]
                            )
                            results.append(
                                {
                                    "title": d.b_path or d.a_path or "diff",
                                    "url": commit_hash,
                                    "snippet": snippet,
                                    "commit": commit_hash,
                                    "author": commit.author.name or "",
                                    "date": commit.committed_datetime.isoformat(),
                                    "diff": part[:2000],
                                }
                            )
                            if len(results) >= max_results:
                                break
                    if len(results) >= max_results:
                        break
                except Exception as exc:  # pragma: no cover - git issues
                    log.warning(f"Failed to get diff for {commit_hash}: {exc}")
                if commit_hash not in indexed:
                    try:
                        conn.execute(
                            "INSERT INTO git_index VALUES (?, ?, ?, ?, ?)",
                            [
                                commit_hash,
                                commit.author.name or "",
                                commit.committed_datetime.isoformat(),
                                commit.message,
                                diff_text,
                            ],
                        )
                        indexed.add(commit_hash)
                    except Exception as exc:  # pragma: no cover - db insert issues
                        log.warning(f"Failed to index commit {commit_hash}: {exc}")

                if query.lower() in commit.message.lower() and len(results) < max_results:
                    msg = commit.message
                    if isinstance(msg, bytes):
                        msg = msg.decode("utf-8", "ignore")
                    snippet = msg.strip()[:200]
                    results.append(
                        {
                            "title": "commit message",
                            "url": commit_hash,
                            "snippet": snippet,
                            "commit": commit_hash,
                            "author": commit.author.name or "",
                            "date": commit.committed_datetime.isoformat(),
                            "diff": diff_text[:2000],
                        }
                    )
                    if len(results) >= max_results:
                        break
    except Exception as exc:  # pragma: no cover - storage unavailable
        log.debug(f"Skipping git_index persistence due to unavailable storage: {exc}")

    return results


@Search.register_embedding_backend("duckdb")
def _duckdb_embedding_backend(
    query_embedding: np.ndarray, max_results: int = 5
) -> List[Dict[str, Any]]:
    """Use local storage for embedding lookups."""

    vec_results = search_storage.vector_search(query_embedding.tolist(), k=max_results)
    formatted: List[Dict[str, Any]] = []
    for r in vec_results:
        claim = search_storage.get_claim(r.get("node_id", "")) or {}
        content = claim.get("content", r.get("content", ""))
        formatted.append(
            {
                "title": content[:60],
                "url": r.get("node_id", ""),
                "snippet": content,
                "embedding": r.get("embedding"),
                "similarity": r.get("similarity"),
            }
        )
    return formatted
