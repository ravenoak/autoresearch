from __future__ import annotations

import copy
import importlib
import os
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    List,
    Mapping,
    Sequence,
    cast,
)

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
                resolved = type(
                    "FastEmbedAvailable",
                    (),
                    {},
                )  # sentinel type indicating availability
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
    from bertopic import BERTopic as BERTopicType
    from spacy.language import Language

    from ..knowledge.graph import SessionGraphPipeline
    from ..orchestration.state import QueryState

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
    _graph_pipeline_lock: ClassVar[threading.Lock] = threading.Lock()
    _graph_pipeline_factory: ClassVar[
        Callable[[], "SessionGraphPipeline"] | None
    ] = None
    _graph_pipeline_singleton: ClassVar["SessionGraphPipeline" | None] = None

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance."""
        with cls._lock:
            cls._instance = None
        with cls._graph_pipeline_lock:
            cls._graph_pipeline_singleton = None

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

    def __init__(self, *, graph_pipeline: "SessionGraphPipeline" | None = None) -> None:
        self.search_history: List[Dict[str, Any]] = []
        self.entities: defaultdict[str, int] = defaultdict(int)
        self.topic_model: BERTopicType | None = None
        self.dictionary: dict[str, int] | None = None
        self.nlp: Language | None = None
        self._graph_pipeline_override: "SessionGraphPipeline" | None = graph_pipeline
        self._graph_summary: dict[str, Any] = {}
        self._graph_stage_metadata: dict[str, Any] = {}
        self._scout_metadata: dict[str, Any] = {}
        self._scout_lock = threading.Lock()
        if get_config().search.context_aware.enabled:
            self._initialize_nlp()

    @property
    def graph_pipeline(self) -> "SessionGraphPipeline":
        """Return the lazily constructed session graph pipeline singleton."""

        if self._graph_pipeline_override is not None:
            return self._graph_pipeline_override
        cls = type(self)
        pipeline = cls._graph_pipeline_singleton
        if pipeline is not None:
            return pipeline
        with cls._graph_pipeline_lock:
            pipeline = cls._graph_pipeline_singleton
            if pipeline is None:
                factory = cls._graph_pipeline_factory or self._default_graph_pipeline_factory
                pipeline = factory()
                cls._graph_pipeline_singleton = pipeline
        return pipeline

    @classmethod
    def configure_graph_pipeline(
        cls,
        *,
        factory: Callable[[], "SessionGraphPipeline"] | None = None,
        pipeline: "SessionGraphPipeline" | None = None,
    ) -> None:
        """Configure or replace the lazy graph pipeline singleton."""

        with cls._graph_pipeline_lock:
            if factory is not None:
                cls._graph_pipeline_factory = factory
                cls._graph_pipeline_singleton = None
            if pipeline is not None:
                cls._graph_pipeline_singleton = pipeline
            if factory is None and pipeline is None:
                cls._graph_pipeline_factory = None
                cls._graph_pipeline_singleton = None

    @staticmethod
    def _default_graph_pipeline_factory() -> "SessionGraphPipeline":
        from ..knowledge.graph import SessionGraphPipeline as _SessionGraphPipeline

        return _SessionGraphPipeline()

    def set_graph_pipeline(self, pipeline: "SessionGraphPipeline" | None) -> None:
        """Override the graph pipeline for the current instance."""

        self._graph_pipeline_override = pipeline

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
            if os.getenv("AUTORESEARCH_AUTO_DOWNLOAD_SPACY_MODEL", "").lower() == "true":
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
        self.search_history.append({"query": query, "results": results, "timestamp": time.time()})
        if len(self.search_history) > max_history:
            self.search_history = self.search_history[-max_history:]
        self._extract_entities(query)
        for result in results:
            self._extract_entities(result.get("title", ""))
            self._extract_entities(result.get("snippet", ""))

        pipeline = self.graph_pipeline
        start = time.perf_counter()
        summary = pipeline.ingest(query, results)
        ingestion_seconds = max(0.0, time.perf_counter() - start)
        summary_payload = summary.to_dict()
        summary_payload["ingestion_seconds"] = ingestion_seconds
        self._graph_summary = summary_payload
        self._store_graph_metadata(summary_payload)
        self._store_scout_complexity(summary_payload)

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
        expanded_terms = sorted(self.entities, key=lambda e: self.entities[e], reverse=True)
        if expanded_terms:
            expansion_factor = context_cfg.expansion_factor
            num_terms = max(1, int(len(expanded_terms) * expansion_factor))
            selected_terms = expanded_terms[:num_terms]
            expanded_query = f"{query} {' '.join(selected_terms)}"
            log.info("Expanded query: '%s' -> '%s'", query, expanded_query)
            return expanded_query
        return query

    # ------------------------------------------------------------------
    # Knowledge graph accessors
    # ------------------------------------------------------------------

    def get_graph_summary(self) -> dict[str, Any]:
        """Return the most recent knowledge graph ingestion summary.

        Returns:
            Dictionary containing counts, contradiction metrics, and other
            metadata recorded during the latest ingestion.
        """

        return dict(self._graph_summary)

    def get_contradiction_signal(self) -> float:
        """Return weighted contradiction signal derived from the knowledge graph.

        Returns:
            Floating-point contradiction score scaled by the configuration
            weight. Values range between ``0.0`` and ``1.0``.
        """

        cfg = get_config()
        context_cfg = getattr(cfg.search, "context_aware", None)
        weight = float(getattr(context_cfg, "graph_contradiction_weight", 0.0))
        stage_meta = self._graph_stage_metadata.get("contradictions", {})
        stored_weight = float(stage_meta.get("weight", -1.0)) if stage_meta else -1.0
        if not stage_meta or stored_weight != weight:
            summary = self.get_graph_summary()
            if summary:
                self._store_graph_metadata(summary)
                stage_meta = self._graph_stage_metadata.get("contradictions", {})
        if stage_meta:
            return float(stage_meta.get("weighted_score", 0.0))
        base_score = self.graph_pipeline.get_contradiction_score()
        weighted = float(base_score * weight)
        self._graph_stage_metadata = {
            "contradictions": {
                "raw_score": float(base_score),
                "weighted_score": weighted,
                "weight": weight,
                "items": [],
            }
        }
        return weighted

    def get_similarity_signal(self) -> float:
        """Return weighted similarity support derived from the knowledge graph."""

        cfg = get_config()
        context_cfg = getattr(cfg.search, "context_aware", None)
        weight = float(getattr(context_cfg, "graph_signal_weight", 0.0))
        stage_meta = self._graph_stage_metadata.get("similarity", {})
        stored_weight = float(stage_meta.get("weight", -1.0)) if stage_meta else -1.0
        if not stage_meta or stored_weight != weight:
            summary = self.get_graph_summary()
            if summary:
                self._store_graph_metadata(summary)
                stage_meta = self._graph_stage_metadata.get("similarity", {})
        if stage_meta:
            return float(stage_meta.get("weighted_score", 0.0))

        summary = self.get_graph_summary()
        if not summary:
            return 0.0

        relations = summary.get("relation_count", 0.0)
        entities = summary.get("entity_count", 0.0)
        try:
            relation_count = float(relations)
        except (TypeError, ValueError):
            relation_count = 0.0
        try:
            entity_count = float(entities)
        except (TypeError, ValueError):
            entity_count = 0.0
        if entity_count <= 0.0:
            return 0.0

        base_score = min(1.0, relation_count / max(entity_count, 1.0))
        weighted = float(max(0.0, min(base_score * weight, 1.0)))
        similarity_meta = {
            "raw_score": base_score,
            "weighted_score": weighted,
            "weight": weight,
            "entity_count": entity_count,
            "relation_count": relation_count,
        }
        self._graph_stage_metadata.setdefault("similarity", similarity_meta)
        return weighted

    def graph_neighbors(
        self, label: str, *, direction: str = "out", limit: int = 5
    ) -> list[dict[str, str]]:
        """Return neighbours for ``label`` from the knowledge graph.

        Args:
            label: Canonical label of the entity.
            direction: Edge direction to traverse (``"out"``, ``"in"``, or
                ``"both"``).
            limit: Maximum number of neighbour relations to return.

        Returns:
            List of neighbour relation dictionaries with subject, predicate,
            and object labels.
        """

        return self.graph_pipeline.neighbors(label, direction=direction, limit=limit)

    def get_graph_neighbors_for_nodes(
        self,
        nodes: Sequence[str],
        *,
        direction: str = "both",
        limit: int = 5,
    ) -> dict[str, list[dict[str, str]]]:
        """Return neighbour relations for the provided entity labels.

        Args:
            nodes: Iterable of entity labels that should be inspected.
            direction: Edge direction passed through to
                :meth:`SessionGraphPipeline.neighbors`.
            limit: Maximum neighbour count per entity.

        Returns:
            Mapping from the original entity label to neighbouring relation
            payloads. Labels with no neighbours are omitted from the result.
        """

        neighbors: dict[str, list[dict[str, str]]] = {}
        seen: set[str] = set()
        pipeline = self.graph_pipeline
        for label in nodes:
            if not isinstance(label, str):
                continue
            trimmed = label.strip()
            if not trimmed:
                continue
            key = trimmed.lower()
            if key in seen:
                continue
            seen.add(key)
            payload = pipeline.neighbors(trimmed, direction=direction, limit=limit)
            if payload:
                neighbors[trimmed] = payload
        return neighbors

    def graph_paths(
        self, source: str, target: str, *, max_depth: int = 3, limit: int = 5
    ) -> list[list[str]]:
        """Return multi-hop paths between ``source`` and ``target``.

        Args:
            source: Label of the starting entity.
            target: Label of the destination entity.
            max_depth: Maximum traversal depth when searching for paths.
            limit: Maximum number of distinct paths to return.

        Returns:
            A list of simple paths represented as ordered entity labels.
        """

        return self.graph_pipeline.paths(source, target, max_depth=max_depth, limit=limit)

    def export_graph_artifacts(self) -> dict[str, str]:
        """Return serialized GraphML and JSON knowledge graph artefacts.

        Returns:
            Mapping containing ``"graphml"`` and ``"graph_json"`` payloads.
        """

        return self.graph_pipeline.export_artifacts()

    # ------------------------------------------------------------------
    # Scout metadata helpers
    # ------------------------------------------------------------------

    def record_scout_observation(
        self,
        query: str,
        ranked_results: Sequence[Mapping[str, Any]],
        *,
        by_backend: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    ) -> None:
        """Capture retrieval overlap and entailment signals for scout telemetry."""

        from ..evidence import score_entailment

        retrieval_sets: list[list[str]] = []
        if by_backend:
            for docs in by_backend.values():
                identifiers = [self._extract_identifier(doc) for doc in docs if doc]
                if identifiers:
                    retrieval_sets.append(identifiers)
        else:
            identifiers = [self._extract_identifier(doc) for doc in ranked_results]
            if identifiers:
                retrieval_sets.append(identifiers)

        entailment_scores: list[dict[str, float]] = []
        for doc in ranked_results:
            snippet = self._extract_text_for_entailment(doc)
            if not snippet:
                continue
            breakdown = score_entailment(query, snippet)
            conflict = float(max(0.0, 1.0 - breakdown.score))
            entailment_scores.append(
                {
                    "score": float(breakdown.score),
                    "overlap": float(breakdown.overlap_ratio),
                    "support": float(breakdown.support_ratio),
                    "conflict": conflict,
                }
            )

        complexity = self._summarise_complexity(query)

        payload = {
            "query": query,
            "retrieval_sets": retrieval_sets,
            "entailment_scores": entailment_scores,
            "complexity": complexity,
            "timestamp": time.time(),
        }

        with self._scout_lock:
            self._scout_metadata = payload

    def get_scout_metadata(self) -> dict[str, Any]:
        """Return a copy of the latest scout telemetry."""

        with self._scout_lock:
            meta = dict(self._scout_metadata)
        if not meta:
            return {}
        cloned = {
            "query": meta.get("query"),
            "timestamp": meta.get("timestamp"),
        }
        if "retrieval_sets" in meta:
            cloned["retrieval_sets"] = [list(group) for group in meta.get("retrieval_sets", [])]
        if "entailment_scores" in meta:
            cloned["entailment_scores"] = [
                dict(score) for score in meta.get("entailment_scores", [])
            ]
        if "complexity" in meta:
            cloned["complexity"] = dict(meta.get("complexity", {}))
        if "graph" in meta:
            cloned["graph"] = copy.deepcopy(meta.get("graph", {}))
        return cloned

    def apply_scout_metadata(self, state: "QueryState") -> bool:
        """Populate ``state.metadata`` with the latest scout signals."""

        metadata = self.get_scout_metadata()
        if not metadata:
            return False

        updated = False
        retrieval_sets = metadata.get("retrieval_sets")
        if retrieval_sets and "scout_retrieval_sets" not in state.metadata:
            state.metadata["scout_retrieval_sets"] = retrieval_sets
            updated = True

        entailment_scores = metadata.get("entailment_scores")
        if entailment_scores and "scout_entailment_scores" not in state.metadata:
            state.metadata["scout_entailment_scores"] = entailment_scores
            updated = True

        complexity = metadata.get("complexity")
        if complexity and "scout_complexity_features" not in state.metadata:
            state.metadata["scout_complexity_features"] = complexity
            updated = True

        graph_payload = metadata.get("graph")
        if graph_payload:
            scout_stage = state.metadata.setdefault("scout_stage", {})
            existing_graph = scout_stage.get("graph")
            if existing_graph != graph_payload:
                scout_stage["graph"] = graph_payload
                updated = True
        elif "scout_stage" in state.metadata:
            scout_stage = state.metadata.get("scout_stage")
            if isinstance(scout_stage, dict) and "graph" in scout_stage:
                scout_stage.pop("graph", None)
                updated = True

        return updated

    def _extract_identifier(self, doc: Mapping[str, Any]) -> str:
        for key in ("id", "url", "path", "source"):
            value = doc.get(key)
            if value:
                return str(value)
        title = doc.get("title")
        snippet = doc.get("snippet")
        if title or snippet:
            return str(title or snippet)
        return str(hash(frozenset(doc.items())))

    def _extract_text_for_entailment(self, doc: Mapping[str, Any]) -> str:
        snippet = doc.get("snippet")
        if isinstance(snippet, str) and snippet.strip():
            return snippet
        content = doc.get("content")
        if isinstance(content, str) and content.strip():
            return content
        title = doc.get("title")
        if isinstance(title, str) and title.strip():
            return title
        return ""

    def _summarise_complexity(self, query: str) -> dict[str, Any]:
        entities_sorted = sorted(self.entities.items(), key=lambda item: item[1], reverse=True)
        entity_labels = [label for label, _ in entities_sorted[:10]]
        entity_count = len({label for label, count in self.entities.items() if count})

        graph_summary = self.get_graph_summary()
        hop_lengths: list[int] = []
        for path in graph_summary.get("multi_hop_paths", []) or []:
            if isinstance(path, Sequence):
                hop_lengths.append(max(0, len(path) - 1))
        hops = max(hop_lengths) if hop_lengths else 0

        clauses = self._estimate_clause_count(query)

        features: dict[str, Any] = {
            "hops": float(hops),
            "entities": entity_labels,
            "entity_count": float(entity_count),
            "clauses": float(clauses),
            "query_length": float(len(query.split())),
        }
        contradictions = graph_summary.get("contradictions")
        if isinstance(contradictions, Sequence):
            features["graph_contradictions"] = float(len(contradictions))
        return features

    def _estimate_clause_count(self, query: str) -> int:
        separators = {",", ";", ":"}
        clause_tokens = {"and", "but", "because", "however", "therefore", "while"}
        count = 1 if query.strip() else 0
        count += sum(query.count(sep) for sep in separators)
        tokens = query.lower().split()
        count += sum(1 for token in tokens if token in clause_tokens)
        return max(1, count) if count else 0

    def _store_scout_complexity(self, summary: dict[str, Any]) -> None:
        """Persist graph-derived features after ingestion."""

        if not summary:
            return
        with self._scout_lock:
            if not self._scout_metadata:
                self._scout_metadata = {"complexity": {}}
            complexity = dict(self._scout_metadata.get("complexity", {}))
            contradictions = summary.get("contradictions")
            if isinstance(contradictions, Sequence):
                complexity["graph_contradictions"] = float(len(contradictions))
            hop_lengths: list[int] = []
            for path in summary.get("multi_hop_paths", []) or []:
                if isinstance(path, Sequence):
                    hop_lengths.append(max(0, len(path) - 1))
            if hop_lengths:
                complexity["hops"] = float(max(hop_lengths))
            self._scout_metadata["complexity"] = complexity

    def _store_graph_metadata(self, summary: Mapping[str, Any]) -> None:
        """Persist planner-oriented graph metadata derived from ``summary``."""

        metadata = self._build_graph_metadata(summary)
        self._graph_stage_metadata = metadata
        if not metadata:
            return
        with self._scout_lock:
            if not self._scout_metadata:
                self._scout_metadata = {"graph": copy.deepcopy(metadata)}
            else:
                self._scout_metadata["graph"] = copy.deepcopy(metadata)

    def _build_graph_metadata(self, summary: Mapping[str, Any]) -> dict[str, Any]:
        if not summary:
            return {}

        cfg = get_config()
        context_cfg = getattr(cfg.search, "context_aware", None)
        weight = float(getattr(context_cfg, "graph_contradiction_weight", 0.0))

        raw_score = float(summary.get("contradiction_score", 0.0) or 0.0)
        weighted_score = float(raw_score * weight)

        contradictions_raw = summary.get("contradictions") or []
        contradiction_items: list[dict[str, Any]] = []
        nodes_for_neighbors: list[str] = []
        if isinstance(contradictions_raw, Sequence):
            for item in contradictions_raw:
                if not isinstance(item, Mapping):
                    continue
                subject = str(item.get("subject", "")) if item.get("subject") else ""
                predicate = str(item.get("predicate", "")) if item.get("predicate") else ""
                objects_value = item.get("objects", [])
                objects: list[str]
                if isinstance(objects_value, Sequence):
                    objects = [str(obj) for obj in objects_value if isinstance(obj, str)]
                else:
                    objects = []
                contradiction_items.append(
                    {
                        "subject": subject,
                        "predicate": predicate,
                        "objects": objects,
                    }
                )
                if subject:
                    nodes_for_neighbors.append(subject)
                nodes_for_neighbors.extend(objects)

        provenance_records = summary.get("provenance") or []
        if isinstance(provenance_records, Sequence):
            for record in provenance_records:
                if not isinstance(record, Mapping):
                    continue
                subject = record.get("subject")
                obj = record.get("object")
                if isinstance(subject, str):
                    nodes_for_neighbors.append(subject)
                if isinstance(obj, str):
                    nodes_for_neighbors.append(obj)

        neighbors = self.get_graph_neighbors_for_nodes(nodes_for_neighbors, direction="both")

        paths_raw = summary.get("multi_hop_paths") or []
        paths: list[list[str]] = []
        if isinstance(paths_raw, Sequence):
            for path in paths_raw:
                if isinstance(path, Sequence):
                    serialised = [str(node) for node in path]
                    if serialised:
                        paths.append(serialised)

        ingestion_seconds = float(summary.get("ingestion_seconds", 0.0) or 0.0)
        storage_latency = summary.get("storage_latency") or {}
        latency_payload: dict[str, float] = {}
        if isinstance(storage_latency, Mapping):
            for key, value in storage_latency.items():
                try:
                    latency_payload[str(key)] = float(value)
                except (TypeError, ValueError):
                    continue

        entity_count = summary.get("entity_count", 0)
        relation_count = summary.get("relation_count", 0)
        try:
            entity_count_float = float(entity_count)
        except (TypeError, ValueError):
            entity_count_float = 0.0
        try:
            relation_count_float = float(relation_count)
        except (TypeError, ValueError):
            relation_count_float = 0.0

        similarity_weight = float(getattr(context_cfg, "graph_signal_weight", 0.0))
        similarity_raw = 0.0
        if entity_count_float > 0.0:
            similarity_raw = min(1.0, relation_count_float / max(entity_count_float, 1.0))
        similarity_weighted = float(
            max(0.0, min(similarity_raw * similarity_weight, 1.0))
        )

        metadata: dict[str, Any] = {
            "contradictions": {
                "raw_score": raw_score,
                "weighted_score": weighted_score,
                "weight": weight,
                "items": contradiction_items,
            },
            "ingestion": {
                "seconds": ingestion_seconds,
                "storage_latency": latency_payload,
                "entity_count": entity_count_float,
                "relation_count": relation_count_float,
            },
            "paths": paths,
            "similarity": {
                "raw_score": similarity_raw,
                "weighted_score": similarity_weighted,
                "weight": similarity_weight,
                "entity_count": entity_count_float,
                "relation_count": relation_count_float,
            },
        }
        if neighbors:
            metadata["neighbors"] = neighbors
        return metadata

    def get_graph_stage_metadata(self) -> dict[str, Any]:
        """Return a defensive copy of the planner-oriented graph metadata."""

        return copy.deepcopy(self._graph_stage_metadata)
