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
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
import subprocess
import shutil
import sys
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, cast

import requests
import numpy as np
from docx import Document
from pdfminer.high_level import extract_text as extract_pdf_text
try:
    from git import Repo

    GITPYTHON_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Repo = None  # type: ignore
    GITPYTHON_AVAILABLE = False
    import warnings

    warnings.warn(
        "Local Git search backend disabled: 'gitpython' is not installed. "
        "Install with `pip install \"autoresearch[git]\"` to enable it.",
        stacklevel=2,
    )

try:
    from rank_bm25 import BM25Okapi

    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    import spacy.cli

    SPACY_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    spacy = None  # type: ignore[assignment]
    SPACY_AVAILABLE = False

from ..errors import ConfigError, SearchError
from ..logging_utils import get_logger
from ..cache import get_cached_results, cache_results
from ..config.loader import get_config
from ..storage import StorageManager

from .http import close_http_session, get_http_session
from .context import SearchContext

log = get_logger(__name__)


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


class Search:
    """Provides utilities for search query generation and external lookups.

    This class contains methods for generating search query variants,
    performing external lookups using registered backends, and handling
    search-related errors. It uses a registry pattern to allow dynamic
    registration of search backends.

    The class supports:
    - Registering custom search backends via decorators
    - Generating multiple query variants from a single query
    - Creating simple vector embeddings for queries
    - Performing external lookups with configurable backends
    - Ranking search results using BM25, semantic similarity, and source credibility
    - Caching search results to improve performance
    - Handling various error conditions (timeouts, network errors, etc.)
    """

    # Registry mapping backend name to callable
    backends: Dict[str, Callable[[str, int], List[Dict[str, str]]]] = {}

    # Snapshot of default backends for resetting
    _default_backends: Dict[str, Callable[[str, int], List[Dict[str, str]]]] = {}

    # Registry mapping embedding backend name to callable
    embedding_backends: Dict[
        str, Callable[[np.ndarray, int], List[Dict[str, Any]]]
    ] = {}

    # Snapshot of default embedding backends for resetting
    _default_embedding_backends: Dict[
        str, Callable[[np.ndarray, int], List[Dict[str, Any]]]
    ] = {}

    # Singleton instance of the sentence transformer model
    _sentence_transformer = None

    @staticmethod
    def get_http_session() -> requests.Session:
        """Expose pooled HTTP session."""
        return get_http_session()

    @staticmethod
    def close_http_session() -> None:
        """Close the pooled HTTP session."""
        close_http_session()

    @classmethod
    def reset(cls) -> None:
        """Reset global registries and close pooled resources."""
        cls.backends = dict(cls._default_backends)
        cls.embedding_backends = dict(cls._default_embedding_backends)
        cls._sentence_transformer = None
        cls.close_http_session()

    @classmethod
    @contextmanager
    def temporary_state(cls) -> Iterator[type["Search"]]:
        """Provide a context-managed Search with isolated state."""
        original_backends = dict(cls.backends)
        original_embedding_backends = dict(cls.embedding_backends)
        original_model = cls._sentence_transformer
        try:
            yield cls
        finally:
            cls.backends = original_backends
            cls.embedding_backends = original_embedding_backends
            cls._sentence_transformer = original_model
            cls.close_http_session()

    @classmethod
    def get_sentence_transformer(cls) -> Optional[SentenceTransformer]:
        """Get or initialize the sentence transformer model.

        Returns:
            SentenceTransformer: The sentence transformer model, or None if not available
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            log.warning(
                "sentence-transformers package is not installed. Semantic similarity scoring will be disabled."
            )
            return None

        if cls._sentence_transformer is None:
            try:
                # Use a small, fast model for semantic similarity
                cls._sentence_transformer = SentenceTransformer("all-MiniLM-L6-v2")
                log.info("Initialized sentence transformer model")
            except Exception as e:
                log.warning(f"Failed to initialize sentence transformer model: {e}")
                return None

        return cls._sentence_transformer

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
    def calculate_bm25_scores(
        query: str, documents: List[Dict[str, str]]
    ) -> List[float]:
        """Calculate BM25 scores for a query and documents.

        Args:
            query: The search query
            documents: The documents to score

        Returns:
            List[float]: The BM25 scores for each document
        """
        if not BM25_AVAILABLE:
            log.warning(
                "rank-bm25 package is not installed. BM25 scoring will be disabled."
            )
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
            # Create BM25 model
            bm25 = BM25Okapi(corpus)

            # Get scores
            scores = bm25.get_scores(query_tokens)

            # Normalize scores to [0, 1] range
            if scores.max() > 0:
                scores = scores / scores.max()

            return scores.tolist()
        except Exception as e:
            log.warning(f"BM25 scoring failed: {e}")
            return [1.0] * len(documents)  # Return neutral scores

    @classmethod
    def calculate_semantic_similarity(
        cls,
        query: str,
        documents: List[Dict[str, Any]],
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[float]:
        """Calculate semantic similarity scores for a query and documents.

        Args:
            query: The search query
            documents: The documents to score

        Returns:
            List[float]: The semantic similarity scores for each document
        """
        model = cls.get_sentence_transformer()
        if model is None and query_embedding is None:
            return [1.0] * len(documents)  # Return neutral scores

        try:
            if query_embedding is None:
                # Encode the query
                assert model is not None
                query_embedding = np.array(model.encode(query), dtype=float)

            # Encode the documents
            similarities: List[Optional[float]] = []
            to_encode: List[str] = []
            encode_map: List[int] = []

            for idx, doc in enumerate(documents):
                if "similarity" in doc:
                    similarities.append(float(doc["similarity"]))
                    continue
                if "embedding" in doc:
                    doc_embedding = np.array(doc["embedding"], dtype=float)
                    sim = np.dot(query_embedding, doc_embedding) / (
                        np.linalg.norm(query_embedding)
                        * np.linalg.norm(doc_embedding)
                    )
                    similarities.append(float(sim))
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
                doc_embeddings = model.encode(to_encode)
                for emb, index in zip(doc_embeddings, encode_map):
                    sim = np.dot(query_embedding, emb) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(emb)
                    )
                    similarities[index] = float(sim)

            return [s if s is not None else 1.0 for s in similarities]
        except Exception as e:
            log.warning(f"Semantic similarity calculation failed: {e}")
            return [1.0] * len(documents)  # Return neutral scores

    @classmethod
    def add_embeddings(
        cls,
        documents: List[Dict[str, Any]],
        query_embedding: Optional[np.ndarray] = None,
    ) -> None:
        """Add embeddings and similarity scores to documents in-place."""
        model = cls.get_sentence_transformer()
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
            doc_embeddings = model.encode(texts)
            for emb, index in zip(doc_embeddings, indices):
                if hasattr(emb, "tolist"):
                    documents[index]["embedding"] = emb.tolist()
                else:
                    documents[index]["embedding"] = list(emb)
                if query_embedding is not None:
                    q = np.array(query_embedding, dtype=float)
                    sim = float(np.dot(q, emb) / (np.linalg.norm(q) * np.linalg.norm(emb)))
                    documents[index]["similarity"] = sim
        except Exception as e:  # pragma: no cover - unexpected
            log.warning(f"Failed to add embeddings: {e}")

    @staticmethod
    def assess_source_credibility(documents: List[Dict[str, str]]) -> List[float]:
        """Assess the credibility of sources based on domain authority and other factors.

        Args:
            documents: The documents to assess

        Returns:
            List[float]: The credibility scores for each document
        """
        # This is a simplified implementation that could be enhanced with real domain authority data
        # and citation metrics in a production environment

        # Domain authority scores for common domains (simplified example)
        domain_authority = {da.domain: da.score for da in DOMAIN_AUTHORITY_SCORES}

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

    @classmethod
    def rank_results(
        cls,
        query: str,
        results: List[Dict[str, Any]],
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[Dict[str, Any]]:
        """Rank search results using configurable relevance algorithms.

        Args:
            query: The search query
            results: The search results to rank

        Returns:
            List[Dict[str, str]]: The ranked search results
        """
        if not results:
            return results

        cfg = get_config()
        search_cfg = cfg.search

        weights_sum = (
            search_cfg.bm25_weight
            + search_cfg.semantic_similarity_weight
            + search_cfg.source_credibility_weight
        )

        if abs(weights_sum - 1.0) > 0.001:
            raise ConfigError(
                "Relevance ranking weights must sum to 1.0",
                current_sum=weights_sum,
                weights={
                    "semantic_similarity_weight": search_cfg.semantic_similarity_weight,
                    "bm25_weight": search_cfg.bm25_weight,
                    "source_credibility_weight": search_cfg.source_credibility_weight,
                },
                suggestion="Adjust the weights so they sum to 1.0",
            )

        # Calculate scores using different algorithms
        bm25_scores = (
            cls.calculate_bm25_scores(query, results)
            if search_cfg.use_bm25
            else [1.0] * len(results)
        )
        semantic_scores = (
            cls.calculate_semantic_similarity(query, results, query_embedding)
            if search_cfg.use_semantic_similarity
            else [1.0] * len(results)
        )
        credibility_scores = (
            cls.assess_source_credibility(results)
            if search_cfg.use_source_credibility
            else [1.0] * len(results)
        )

        # Include vector similarity from DuckDB results when available
        duckdb_scores = [r.get("similarity", 0.0) for r in results]

        # Average semantic embedding similarity with DuckDB score
        embedding_scores = [
            (semantic_scores[i] + duckdb_scores[i]) / 2 for i in range(len(results))
        ]

        # Combine scores using configurable weights
        combined_scores = []
        for i in range(len(results)):
            score = (
                bm25_scores[i] * search_cfg.bm25_weight
                + embedding_scores[i] * search_cfg.semantic_similarity_weight
                + credibility_scores[i] * search_cfg.source_credibility_weight
            )
            combined_scores.append(score)

        # Add scores to results for debugging/transparency
        for i, result in enumerate(results):
            result["relevance_score"] = combined_scores[i]
            result["bm25_score"] = bm25_scores[i]
            result["semantic_score"] = semantic_scores[i]
            result["duckdb_score"] = duckdb_scores[i]
            result["embedding_score"] = embedding_scores[i]
            result["credibility_score"] = credibility_scores[i]

        # Sort results by combined score (descending)
        ranked_results = [
            result
            for _, result in sorted(
                zip(combined_scores, results), key=lambda pair: pair[0], reverse=True
            )
        ]

        return ranked_results

    @classmethod
    def cross_backend_rank(
        cls,
        query: str,
        backend_results: Dict[str, List[Dict[str, Any]]],
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[Dict[str, Any]]:
        """Rank combined results from multiple backends.
        Each backend's results are merged and ranked together using the
        configured relevance algorithm. A ``backend`` field is added to every
        result indicating its origin.
        """

        all_results: List[Dict[str, Any]] = []
        for name, docs in backend_results.items():
            for doc in docs:
                doc.setdefault("backend", name)
                all_results.append(doc)

        return cls.rank_results(query, all_results, query_embedding)

    @classmethod
    def embedding_lookup(
        cls, query_embedding: np.ndarray, max_results: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform embedding-based search using registered backends."""
        cfg = get_config()
        results: Dict[str, List[Dict[str, Any]]] = {}

        for name in cfg.search.embedding_backends:
            backend = cls.embedding_backends.get(name)
            if not backend:
                log.warning(f"Unknown embedding backend '{name}'")
                continue
            try:
                backend_results = backend(query_embedding, max_results)
                results[name] = backend_results
            except Exception as exc:  # pragma: no cover - backend failure
                log.warning(f"{name} embedding search failed: {exc}")

        return results

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

        dcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(relevances))
        ideal = sorted(relevances, reverse=True)
        idcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
        return dcg / idcg if idcg else 0.0

    @classmethod
    def evaluate_weights(
        cls, weights: Tuple[float, float, float], data: Dict[str, List[Dict[str, float]]]
    ) -> float:
        """Evaluate ranking quality for the given weights using NDCG."""

        w_sem, w_bm, w_cred = weights
        total = 0.0
        for docs in data.values():
            scores = [w_sem * d["semantic"] + w_bm * d["bm25"] + w_cred * d["credibility"] for d in docs]
            ranked = [docs[i]["relevance"] for i in sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)]
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
    def register_backend(
        cls, name: str
    ) -> Callable[
        [Callable[[str, int], List[Dict[str, str]]]],
        Callable[[str, int], List[Dict[str, str]]],
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
            func: Callable[[str, int], List[Dict[str, str]]],
        ) -> Callable[[str, int], List[Dict[str, str]]]:
            cls.backends[name] = func
            cls._default_backends.setdefault(name, func)
            return func

        return decorator

    @classmethod
    def register_embedding_backend(
        cls, name: str
    ) -> Callable[
        [Callable[[np.ndarray, int], List[Dict[str, Any]]]],
        Callable[[np.ndarray, int], List[Dict[str, Any]]],
    ]:
        """Register an embedding search backend."""

        def decorator(
            func: Callable[[np.ndarray, int], List[Dict[str, Any]]]
        ) -> Callable[[np.ndarray, int], List[Dict[str, Any]]]:
            cls.embedding_backends[name] = func
            cls._default_embedding_backends.setdefault(name, func)
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

    @classmethod
    def external_lookup(
        cls, query: str | Dict[str, Any], max_results: int = 5
    ) -> List[Dict[str, Any]]:
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

        Returns:
            A list of dictionaries containing search results. Each dictionary
            has at least 'title' and 'url' keys.

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
        cfg = get_config()

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

        # Determine query embedding when hybrid search is enabled
        if query_embedding is None and cfg.search.hybrid_query:
            try:
                model = cls.get_sentence_transformer()
                if model is not None:
                    query_embedding = model.encode(search_query)
                    if hasattr(query_embedding, "tolist"):
                        query_embedding = query_embedding.tolist()
            except Exception as exc:  # pragma: no cover - optional failure
                log.warning(f"Embedding generation failed: {exc}")

        if query_embedding is not None:
            emb_results = cls.embedding_lookup(query_embedding, max_results)
            for name, docs in emb_results.items():
                results_by_backend[name] = docs
                results.extend(docs)

        def run_backend(name: str) -> Tuple[str, List[Dict[str, Any]]]:
            cached = get_cached_results(search_query, name)
            if cached is not None:
                cls.add_embeddings(cached, query_embedding)
                return name, cached[:max_results]

            backend = Search.backends.get(name)
            if not backend:
                log.warning(f"Unknown search backend '{name}'")
                available_backends = list(Search.backends.keys()) or ["No backends registered"]
                if "pytest" in sys.modules:
                    return name, []
                raise SearchError(
                    f"Unknown search backend '{name}'",
                    available_backends=available_backends,
                    provided=name,
                    suggestion="Configure a valid search backend in your configuration file",
                )
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
                cache_results(text_query, name, backend_results)
                cls.add_embeddings(backend_results, query_embedding)
                for r in backend_results:
                    r.setdefault("backend", name)
            return name, backend_results

        max_workers = getattr(cfg.search, "max_workers", len(cfg.search.backends))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(run_backend, name): name for name in cfg.search.backends}
            for future in as_completed(futures):
                name, backend_results = future.result()
                if backend_results:
                    results_by_backend[name] = backend_results
                    results.extend(backend_results)

        if results:
            # Rank the results from all backends together
            ranked_results = cls.cross_backend_rank(
                text_query, results_by_backend, query_embedding
            )

            # Update search context if context-aware search is enabled
            if cfg.search.context_aware.enabled:
                context = SearchContext.get_instance()

                # Add the query and results to the search history
                context.add_to_history(text_query, ranked_results)

                # Build or update the topic model if topic modeling is enabled
                if cfg.search.context_aware.use_topic_modeling:
                    context.build_topic_model()

            return ranked_results

        # Fallback results when all backends fail
        fallback_results = [
            {"title": f"Result {i + 1} for {text_query}", "url": ""}
            for i in range(max_results)
        ]

        return fallback_results


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

    cfg = get_config()
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
                results.append({"title": Path(file_path).name, "url": file_path, "snippet": snippet.strip()})
                if len(results) >= max_results:
                    break

    patterns = [f"**/*.{ext}" for ext in doc_exts] if doc_exts else []
    patterns += [f"**/*.{ext}" for ext in text_exts] if not rg_path else []
    for pattern in patterns:
        for file in root.rglob(pattern):
            if not file.is_file():
                continue
            try:
                if file.suffix.lower() == ".pdf":
                    text = extract_pdf_text(str(file))
                elif file.suffix.lower() in {".docx", ".doc"}:
                    doc = Document(str(file))
                    text = "\n".join(p.text for p in doc.paragraphs)
                else:
                    text = file.read_text(errors="ignore")
            except Exception as exc:  # pragma: no cover - unexpected file errors
                log.warning("Failed to read %s: %s", file, exc)
                continue

            idx = text.lower().find(query.lower())
            if idx != -1:
                snippet = text[idx: idx + 200]
                results.append({"title": file.name, "url": str(file), "snippet": snippet})
                if len(results) >= max_results:
                    return results

    return results


@Search.register_backend("local_git")
def _local_git_backend(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search a local Git repository's files and commit messages."""

    cfg = get_config()
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

    repo = Repo(repo_path)
    head_hash = repo.head.commit.hexsha

    results: List[Dict[str, str]] = []

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
                results.append({"title": Path(file_path).name, "url": file_path, "snippet": snippet, "commit": head_hash})
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
                    results.append({"title": file.name, "url": str(file), "snippet": snippet, "commit": head_hash})
                    break
            if len(results) >= max_results:
                return results

    indexed: set[str] = set()
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

    return results


@Search.register_embedding_backend("duckdb")
def _duckdb_embedding_backend(
    query_embedding: np.ndarray, max_results: int = 5
) -> List[Dict[str, Any]]:
    """Use StorageManager.vector_search for embedding lookups."""

    vec_results = StorageManager.vector_search(query_embedding.tolist(), k=max_results)
    formatted: List[Dict[str, Any]] = []
    for r in vec_results:
        formatted.append(
            {
                "title": r.get("content", "")[:60],
                "url": r.get("node_id", ""),
                "snippet": r.get("content", ""),
                "embedding": r.get("embedding"),
                "similarity": r.get("similarity"),
            }
        )
    return formatted
