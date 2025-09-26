"""Helper utilities for ontology reasoning and advanced SPARQL queries."""

from __future__ import annotations

from importlib import import_module
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

import hashlib
import logging
import re
import threading
import time
import warnings
from collections import defaultdict
import networkx as nx
import rdflib

try:  # pragma: no cover - optional dependency
    import owlrl
except Exception:  # pragma: no cover - fallback for offline tests
    class _DeductiveClosure:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """No-op constructor for fallback reasoner."""

        def expand(self, graph: rdflib.Graph) -> None:
            """No-op expansion when owlrl is unavailable."""

    @dataclass(frozen=True)
    class OwlRLStub:
        OWLRL_Semantics: object
        RDFS_Semantics: object
        DeductiveClosure: type

    owlrl = OwlRLStub(  # type: ignore
        OWLRL_Semantics=object(),
        RDFS_Semantics=object(),
        DeductiveClosure=_DeductiveClosure,
    )
    warnings.warn(
        "owlrl not installed; ontology reasoning will be skipped",
        RuntimeWarning,
    )

from .config import ConfigLoader
from .errors import StorageError


# Registry for pluggable ontology reasoners
_REASONER_PLUGINS: Dict[str, Callable[[rdflib.Graph], None]] = {}


def register_reasoner(
    name: str,
) -> Callable[[Callable[[rdflib.Graph], None]], Callable[[rdflib.Graph], None]]:
    """Register a reasoning plugin for use in the ontology pipeline.

    Args:
        name: Identifier under which the decorated callable is stored.

    Returns:
        A decorator that stores the wrapped callable in the global reasoner
        registry, keyed by ``name``.
    """

    def decorator(func: Callable[[rdflib.Graph], None]) -> Callable[[rdflib.Graph], None]:
        _REASONER_PLUGINS[name] = func
        return func

    return decorator


@register_reasoner("owlrl")
def _owlrl_reasoner(store: rdflib.Graph) -> None:
    """Apply OWL RL reasoning using ``owlrl`` if available."""

    try:  # pragma: no cover - optional dependency
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(store)
    except Exception as exc:  # pragma: no cover - optional dependency
        raise StorageError(
            "Failed to apply owlrl reasoning",
            cause=exc,
            suggestion="Ensure the owlrl package is installed",
        )


@register_reasoner("rdfs")
def _rdfs_reasoner(store: rdflib.Graph) -> None:
    """Apply RDFS reasoning using ``owlrl`` if available."""

    try:  # pragma: no cover - optional dependency
        owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(store)
    except Exception as exc:  # pragma: no cover - optional dependency
        raise StorageError(
            "Failed to apply RDFS reasoning",
            cause=exc,
            suggestion="Ensure the owlrl package is installed",
        )


def run_ontology_reasoner(
    store: rdflib.Graph, engine: Optional[str] = None
) -> None:
    """Apply ontology reasoning using the configured engine.

    Args:
        store: RDF graph that should be enriched with inferred triples.
        engine: Optional override for the reasoner name. When ``None`` the
            value from configuration is used.

    Raises:
        StorageError: If the configured reasoner is unknown, times out, or
            encounters an unrecoverable error during execution.
    """

    storage_cfg = ConfigLoader().config.storage
    reasoner_setting = engine or getattr(storage_cfg, "ontology_reasoner", "owlrl")
    reasoner = str(reasoner_setting)

    logger = logging.getLogger(__name__)
    triple_count = len(store)
    logger.info(
        "Starting ontology reasoning with %d triples using %s", triple_count, reasoner
    )

    max_triples = getattr(storage_cfg, "ontology_reasoner_max_triples", None)
    if max_triples is not None and triple_count > max_triples:
        logger.warning(
            "Skipping ontology reasoning for %d triples; limit is %d",
            triple_count,
            max_triples,
        )
        return

    start_time = time.perf_counter()

    def _apply_reasoner() -> None:
        if reasoner in _REASONER_PLUGINS:
            _REASONER_PLUGINS[reasoner](store)
        elif ":" in reasoner:  # pragma: no cover - external reasoners optional
            try:
                module, func = reasoner.split(":", maxsplit=1)
                mod = import_module(module)
                getattr(mod, func)(store)
            except Exception as exc:  # pragma: no cover - import failures optional
                raise StorageError(
                    "Failed to run external ontology reasoner",
                    cause=exc,
                    suggestion="Check storage.ontology_reasoner configuration",
                )
        else:
            raise StorageError(
                f"Unknown ontology reasoner: {reasoner}",
                suggestion=(
                    "Register the reasoner via register_reasoner or use 'module:function'"
                ),
            )

    error: list[BaseException] = []

    def _worker() -> None:
        try:
            _apply_reasoner()
        except BaseException as exc:  # capture all exceptions including KeyboardInterrupt
            error.append(exc)

    timeout = getattr(storage_cfg, "ontology_reasoner_timeout", None)

    if timeout is None:
        _worker()
    else:
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            raise StorageError(
                f"Ontology reasoner '{reasoner}' timed out after {timeout} seconds",
                suggestion=(
                    "Increase storage.ontology_reasoner_timeout or choose a lighter reasoner"
                ),
            )
        thread.join()

    if error:
        exc = error[0]
        if isinstance(exc, StorageError):
            raise exc
        if isinstance(exc, KeyboardInterrupt):
            raise StorageError(
                "Ontology reasoning interrupted",
                suggestion=(
                    "Adjust storage.ontology_reasoner_timeout or choose a lighter reasoner"
                ),
            ) from exc
        cause = exc if isinstance(exc, Exception) else None
        raise StorageError(
            f"Failed to apply {reasoner} reasoning",
            cause=cause,
            suggestion="Ensure the ontology reasoner plugin is correctly installed",
        ) from exc

    elapsed = time.perf_counter() - start_time
    logger.info(
        "Completed ontology reasoning with %d triples in %.2f seconds",
        len(store),
        elapsed,
    )


def query_with_reasoning(
    store: rdflib.Graph, query: str, engine: Optional[str] = None
):
    """Run a SPARQL query with ontology reasoning applied first.

    Args:
        store: RDF graph to query.
        query: SPARQL query string executed after reasoning.
        engine: Optional override for the reasoner name.

    Returns:
        The ``rdflib`` query result produced by evaluating ``query`` on the
        enriched ``store``.

    Raises:
        StorageError: If ontology reasoning fails before the query executes.
    """

    run_ontology_reasoner(store, engine)
    return store.query(query)


def _slugify(label: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return cleaned or "entity"


def _make_entity_id(label: str) -> str:
    normalized = label.strip().lower()
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"kg:{_slugify(label)}:{digest}"


def _normalise_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sentence_split(text: str) -> list[str]:
    tokens = re.split(r"[.!?]+\s+", text)
    return [token.strip() for token in tokens if token.strip()]


def _truncate_snippet(snippet: str, limit: int = 240) -> str:
    snippet = _normalise_whitespace(snippet)
    if len(snippet) <= limit:
        return snippet
    return f"{snippet[:limit - 1].rstrip()}…"


def _clean_entity(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" .,;:'\"()")


@dataclass
class GraphEntity:
    """Structured representation of an extracted entity."""

    id: str
    label: str
    type: str = "entity"
    source: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "attributes": dict(self.attributes),
        }
        if self.source:
            payload["source"] = self.source
        return payload


@dataclass
class GraphRelation:
    """Structured representation of a semantic relation."""

    subject_id: str
    predicate: str
    object_id: str
    weight: float = 1.0
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "object_id": self.object_id,
            "weight": self.weight,
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True)
class GraphContradiction:
    """Detected contradiction derived from knowledge graph triples."""

    subject: str
    predicate: str
    objects: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "objects": list(self.objects),
        }


@dataclass
class GraphExtractionSummary:
    """Summary describing the outcome of a graph ingestion run."""

    entity_count: int
    relation_count: int
    contradictions: list[GraphContradiction]
    multi_hop_paths: list[list[str]]
    query: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "multi_hop_paths": [list(path) for path in self.multi_hop_paths],
            "query": self.query,
            "timestamp": self.timestamp,
            "contradiction_score": self.contradiction_score,
        }

    @property
    def contradiction_score(self) -> float:
        if self.relation_count == 0:
            return 0.0
        return min(1.0, len(self.contradictions) / self.relation_count)


class KnowledgeGraphPipeline:
    """Extract entities and relations from retrieval snippets.

    The pipeline normalises raw snippets, identifies entity and relation
    candidates, persists them, and exposes derived metrics such as detected
    contradictions or multi-hop paths.
    """

    def __init__(self) -> None:
        self._entity_cache: dict[str, GraphEntity] = {}
        self._entity_lock = threading.Lock()
        self._summary_lock = threading.Lock()
        self._latest_summary: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(
        self,
        query: str,
        snippets: Sequence[Mapping[str, Any]],
    ) -> GraphExtractionSummary:
        """Extract graph data from retrieved snippets and persist it.

        Args:
            query: Original retrieval query that produced ``snippets``.
            snippets: Iterable of snippet payloads that include title, snippet
                text, and optional URL metadata.

        Returns:
            A :class:`GraphExtractionSummary` describing how many entities and
            relations were added plus any detected contradictions or
            multi-hop paths.
        """

        cfg = ConfigLoader().config
        context_cfg = getattr(getattr(cfg, "search", None), "context_aware", None)
        enabled = bool(getattr(context_cfg, "enabled", False))
        pipeline_enabled = bool(getattr(context_cfg, "graph_pipeline_enabled", enabled))
        if not pipeline_enabled:
            summary = GraphExtractionSummary(0, 0, [], [], query=query)
            self._store_summary(summary)
            return summary

        max_entities = int(getattr(context_cfg, "graph_max_entities", 256))
        max_relations = int(getattr(context_cfg, "graph_max_edges", 512))

        entities: dict[str, GraphEntity] = {}
        relations: list[GraphRelation] = []
        triples: list[tuple[str, str, str]] = []
        relation_keys: set[tuple[str, str, str]] = set()

        for snippet in snippets:
            if len(relations) >= max_relations:
                break
            text_parts = [snippet.get("title"), snippet.get("snippet"), snippet.get("content")]
            for raw_text in text_parts:
                text = _normalise_whitespace(raw_text or "")
                if not text:
                    continue
                sentences = _sentence_split(text)
                for sentence in sentences:
                    extracted = self._extract_relations(sentence)
                    for subj_label, predicate, obj_label in extracted:
                        if not subj_label or not obj_label:
                            continue
                        subject = self._ensure_entity(subj_label, snippet.get("url"))
                        obj = self._ensure_entity(obj_label, snippet.get("url"))
                        if subject.id not in entities and len(entities) >= max_entities:
                            continue
                        if obj.id not in entities and len(entities) >= max_entities:
                            continue
                        entities[subject.id] = subject
                        entities[obj.id] = obj

                        relation_key = (subject.id, predicate, obj.id)
                        if relation_key in relation_keys:
                            continue
                        relation_keys.add(relation_key)

                        provenance = {
                            "snippet": _truncate_snippet(text),
                            "source": snippet.get("url") or snippet.get("backend"),
                        }
                        relation = GraphRelation(
                            subject_id=subject.id,
                            predicate=predicate,
                            object_id=obj.id,
                            provenance=provenance,
                        )
                        relations.append(relation)
                        triples.append((subject.id, predicate, obj.id))
                        if len(relations) >= max_relations:
                            break
                    if len(relations) >= max_relations:
                        break

        summary = GraphExtractionSummary(
            entity_count=len(entities),
            relation_count=len(relations),
            contradictions=[],
            multi_hop_paths=[],
            query=query,
        )

        if not relations and not entities:
            self._store_summary(summary)
            return summary

        try:
            from .storage import StorageManager  # Local import to avoid circular dependency

            StorageManager.update_knowledge_graph(
                entities=[entity.to_payload() for entity in entities.values()],
                relations=[relation.to_payload() for relation in relations],
                triples=triples,
            )

            kg_graph = StorageManager.get_knowledge_graph(create=False)
            summary.contradictions = self._detect_contradictions(kg_graph)
            summary.multi_hop_paths = self._derive_multi_hop_paths(kg_graph)
        except Exception as exc:  # pragma: no cover - defensive logging
            logging.getLogger(__name__).debug(
                "Knowledge graph ingestion failed", exc_info=exc
            )

        self._store_summary(summary)
        return summary

    def get_latest_summary(self) -> dict[str, Any]:
        """Return the most recent ingestion summary.

        Returns:
            A shallow copy of the latest graph extraction summary payload.
        """

        with self._summary_lock:
            return dict(self._latest_summary)

    def get_contradiction_score(self) -> float:
        """Return the current contradiction score from the summary.

        Returns:
            Normalised contradiction score in the range ``[0.0, 1.0]``.
        """

        summary = self.get_latest_summary()
        score = summary.get("contradiction_score")
        if isinstance(score, (int, float)):
            return float(score)
        return 0.0

    def neighbors(
        self,
        entity_label: str,
        *,
        direction: str = "out",
        limit: int = 5,
    ) -> list[dict[str, str]]:
        """Return neighbouring entities linked to ``entity_label``.

        Args:
            entity_label: Canonical label of the entity to search for.
            direction: Restrict traversal to ``"out"``, ``"in"``, or
                ``"both"`` directions.
            limit: Maximum number of neighbours returned.

        Returns:
            A list of neighbour records describing adjacent entities and the
            predicates connecting them.
        """

        try:
            from .storage import StorageManager

            graph = StorageManager.get_knowledge_graph(create=False)
        except Exception:
            return []
        if graph is None:
            return []

        matches = self._find_nodes_by_label(graph, entity_label)
        results: list[dict[str, str]] = []
        for node in matches:
            if direction == "in":
                iterator = graph.in_edges(node, keys=True, data=True)
            elif direction == "both":
                iterator = list(graph.out_edges(node, keys=True, data=True)) + list(
                    graph.in_edges(node, keys=True, data=True)
                )
            else:
                iterator = graph.out_edges(node, keys=True, data=True)
            for source, target, key, data in iterator:
                predicate = data.get("predicate") or key
                other = target if source == node else source
                label = graph.nodes[other].get("label", other)
                results.append({
                    "subject": graph.nodes[source].get("label", source),
                    "predicate": predicate,
                    "object": graph.nodes[target].get("label", target),
                    "direction": "out" if source == node else "in",
                    "target": label,
                })
                if len(results) >= limit:
                    return results
        return results

    def find_paths(
        self,
        source_label: str,
        target_label: str,
        *,
        max_depth: int = 3,
        limit: int = 5,
    ) -> list[list[str]]:
        """Return simple paths between two entity labels.

        Args:
            source_label: Label of the starting entity.
            target_label: Label of the destination entity.
            max_depth: Maximum traversal depth when searching for paths.
            limit: Maximum number of distinct paths to return.

        Returns:
            A list of paths where each path is represented as ordered labels
            traversed from source to target.
        """

        try:
            from .storage import StorageManager

            graph = StorageManager.get_knowledge_graph(create=False)
        except Exception:
            return []
        if graph is None:
            return []

        sources = self._find_nodes_by_label(graph, source_label)
        targets = self._find_nodes_by_label(graph, target_label)
        if not sources or not targets:
            return []

        undirected = graph.to_undirected(as_view=True)
        label_lookup = {node: graph.nodes[node].get("label", node) for node in graph.nodes}
        paths: list[list[str]] = []
        for source in sources:
            for target in targets:
                if source == target:
                    continue
                try:
                    iterator = nx.all_simple_paths(undirected, source, target, cutoff=max_depth)
                except Exception:
                    continue
                for path in iterator:
                    if len(path) < 2:
                        continue
                    labelled = [label_lookup.get(node, str(node)) for node in path]
                    if labelled not in paths:
                        paths.append(labelled)
                    if len(paths) >= limit:
                        return paths
        return paths

    def export_artifacts(self) -> dict[str, str]:
        """Return GraphML and JSON artefacts for downstream consumers.

        Returns:
            Mapping of artifact format to serialised string content.
        """

        try:
            from .storage import StorageManager

            graphml = StorageManager.export_knowledge_graph_graphml()
            graph_json = StorageManager.export_knowledge_graph_json()
        except Exception:  # pragma: no cover - optional storage errors
            graphml = ""
            graph_json = "{}"
        return {"graphml": graphml, "graph_json": graph_json}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _store_summary(self, summary: GraphExtractionSummary) -> None:
        with self._summary_lock:
            self._latest_summary = summary.to_dict()

    def _ensure_entity(self, label: str, source: Optional[str]) -> GraphEntity:
        key = label.strip().lower()
        with self._entity_lock:
            entity = self._entity_cache.get(key)
            if entity is None:
                entity = GraphEntity(
                    id=_make_entity_id(label),
                    label=label,
                    source=source,
                )
                self._entity_cache[key] = entity
            elif source and not entity.source:
                entity.source = source
        return entity

    def _extract_relations(self, sentence: str) -> list[tuple[str, str, str]]:
        sentence = _normalise_whitespace(sentence)
        relations: list[tuple[str, str, str]] = []
        if not sentence:
            return relations

        # Direct verb patterns such as "A discovered B"
        verb_pattern = re.compile(
            (
                r"(?P<subj>[A-Z][A-Za-z0-9 .'-]+?)\s+"
                r"(?P<verb>discovered|invented|created|developed|founded|built|"
                r"wrote|directed|led|studied|isolated)\s+"
                r"(?P<obj>[A-Za-z][A-Za-z0-9 .'-]+)"
            ),
            re.IGNORECASE,
        )
        for match in verb_pattern.finditer(sentence):
            subj = _clean_entity(match.group("subj"))
            obj = _clean_entity(match.group("obj"))
            if " with " in obj.lower():
                continue
            verb = match.group("verb").lower().replace(" ", "_")
            if subj and obj:
                relations.append((subj, verb, obj))

        # Collaborations "A worked with B" or "A discovered X with B"
        collab_pattern = re.compile(
            (
                r"(?P<subj>[A-Z][A-Za-z0-9 .'-]+?)\s+"
                r"(?:collaborated|worked|partnered)\s+with\s+"
                r"(?P<obj>[A-Z][A-Za-z0-9 .'-]+)"
            ),
            re.IGNORECASE,
        )
        for match in collab_pattern.finditer(sentence):
            subj = _clean_entity(match.group("subj"))
            obj = _clean_entity(match.group("obj"))
            if subj and obj:
                relations.append((subj, "collaborated_with", obj))
                relations.append((obj, "collaborated_with", subj))

        with_pattern = re.compile(
            (
                r"(?P<subj>[A-Z][A-Za-z0-9 .'-]+?)\s+"
                r"(?P<verb>discovered|invented|created|developed|built|wrote)\s+"
                r"(?P<object>[A-Za-z][A-Za-z0-9 .'-]+?)(?=\s+with\s+)\s+with\s+"
                r"(?P<partner>[A-Z][A-Za-z0-9 .'-]+)"
            ),
            re.IGNORECASE,
        )
        for match in with_pattern.finditer(sentence):
            subj = _clean_entity(match.group("subj"))
            obj = _clean_entity(match.group("object"))
            partner = _clean_entity(match.group("partner"))
            verb = match.group("verb").lower().replace(" ", "_")
            if subj and obj:
                relations.append((subj, verb, obj))
            if subj and partner:
                relations.append((subj, "collaborated_with", partner))
            if partner and subj:
                relations.append((partner, "collaborated_with", subj))

        born_pattern = re.compile(
            (
                r"(?P<subj>[A-Z][A-Za-z0-9 .'-]+?)\s+"
                r"(?:was|is)\s+born\s+in\s+(?P<obj>[A-Z][A-Za-z0-9 .'-]+)"
            ),
            re.IGNORECASE,
        )
        for match in born_pattern.finditer(sentence):
            subj = _clean_entity(match.group("subj"))
            obj = _clean_entity(match.group("obj"))
            if subj and obj:
                relations.append((subj, "born_in", obj))

        role_pattern = re.compile(
            (
                r"(?P<subj>[A-Z][A-Za-z0-9 .'-]+?)\s+"
                r"(?:is|was)\s+(?:an?\s+)?(?P<role>[A-Za-z\s]+?)\s+"
                r"(?P<prep>of|in|at|for)\s+(?P<obj>[A-Z][A-Za-z0-9 .'-]+)"
            ),
            re.IGNORECASE,
        )
        for match in role_pattern.finditer(sentence):
            subj = _clean_entity(match.group("subj"))
            obj = _clean_entity(match.group("obj"))
            role = match.group("role").strip().replace(" ", "_").lower()
            prep = match.group("prep").lower()
            predicate = f"{role}_{prep}" if role else f"related_{prep}"
            if subj and obj:
                relations.append((subj, predicate, obj))

        married_pattern = re.compile(
            (
                r"(?P<subj>[A-Z][A-Za-z0-9 .'-]+?)\s+"
                r"(?:married|marry)\s+(?P<obj>[A-Z][A-Za-z0-9 .'-]+)"
            ),
            re.IGNORECASE,
        )
        for match in married_pattern.finditer(sentence):
            subj = _clean_entity(match.group("subj"))
            obj = _clean_entity(match.group("obj"))
            if subj and obj:
                relations.append((subj, "married", obj))
                relations.append((obj, "married", subj))

        return relations

    def _detect_contradictions(self, graph: Any) -> list[GraphContradiction]:
        if graph is None:
            try:
                from .storage import StorageManager

                graph = StorageManager.get_knowledge_graph(create=False)
            except Exception:
                return []
        if graph is None:
            return []

        buckets: dict[tuple[str, str], set[str]] = defaultdict(set)
        label_lookup = {node: graph.nodes[node].get("label", node) for node in graph.nodes}
        for subj, obj, key, data in graph.edges(keys=True, data=True):
            predicate = data.get("predicate") or key
            subj_label = label_lookup.get(subj, str(subj))
            obj_label = label_lookup.get(obj, str(obj))
            buckets[(subj_label, predicate)].add(obj_label)

        contradictions: list[GraphContradiction] = []
        for (subject, predicate), objects in buckets.items():
            if len(objects) > 1:
                contradictions.append(
                    GraphContradiction(
                        subject=subject,
                        predicate=predicate,
                        objects=tuple(sorted(objects)),
                    )
                )
        return contradictions

    def _derive_multi_hop_paths(self, graph: Any) -> list[list[str]]:
        if graph is None:
            try:
                from .storage import StorageManager

                graph = StorageManager.get_knowledge_graph(create=False)
            except Exception:
                return []
        if graph is None:
            return []
        undirected = graph.to_undirected(as_view=True)
        label_lookup = {node: graph.nodes[node].get("label", node) for node in graph.nodes}
        paths: list[list[str]] = []
        for source in graph.nodes:
            for target in graph.nodes:
                if source == target:
                    continue
                try:
                    for path in nx.all_simple_paths(undirected, source, target, cutoff=3):
                        if len(path) < 3:
                            continue
                        labelled = [label_lookup.get(node, str(node)) for node in path]
                        if labelled not in paths:
                            paths.append(labelled)
                        if len(paths) >= 5:
                            return paths
                except Exception:
                    continue
        return paths

    def _find_nodes_by_label(self, graph: Any, label: str) -> list[str]:
        normalized = label.strip().lower()
        matches = []
        for node, attrs in graph.nodes(data=True):
            node_label = str(attrs.get("label", node)).strip().lower()
            if node_label == normalized:
                matches.append(node)
        return matches


__all__ = [
    "run_ontology_reasoner",
    "query_with_reasoning",
    "register_reasoner",
    "KnowledgeGraphPipeline",
]
