"""Session-scoped knowledge graph pipeline utilities.

The pipeline extracts lightweight entities and relations from retrieval
snippets, persists them through the shared :mod:`autoresearch.storage`
backends, and exposes traversal helpers for downstream reasoning. All public
APIs provide Google-style docstrings and explicit typing to satisfy the
repository conventions documented in ``src/AGENTS.md``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
import logging
import re
import threading
import time
from types import MethodType, SimpleNamespace
from typing import Any, Callable, Mapping, Sequence

import networkx as nx

from ..config import ConfigLoader

log = logging.getLogger(__name__)


def _slugify(label: str) -> str:
    """Return a filesystem-friendly slug derived from ``label``."""

    cleaned = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return cleaned or "entity"


def _make_entity_id(label: str) -> str:
    """Return a deterministic identifier for ``label``."""

    normalized = label.strip().lower()
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"kg:{_slugify(label)}:{digest}"


def _normalise_whitespace(text: str) -> str:
    """Collapse consecutive whitespace characters in ``text``."""

    return re.sub(r"\s+", " ", text or "").strip()


def _sentence_split(text: str) -> list[str]:
    """Return a naive sentence split for ``text``."""

    tokens = re.split(r"[.!?]+\s+", text)
    return [token.strip() for token in tokens if token.strip()]


def _truncate_snippet(snippet: str, limit: int = 240) -> str:
    """Return an abbreviated ``snippet`` capped at ``limit`` characters."""

    snippet = _normalise_whitespace(snippet)
    if len(snippet) <= limit:
        return snippet
    return f"{snippet[:limit - 1].rstrip()}…"


def _clean_entity(value: str) -> str:
    """Normalise entity labels extracted from snippets."""

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
        """Return a serialisable payload suitable for persistence."""

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
        """Return a serialisable payload suitable for persistence."""

        return {
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "object_id": self.object_id,
            "weight": self.weight,
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True)
class GraphContradiction:
    """Contradiction derived from mutually exclusive relations."""

    subject: str
    predicate: str
    objects: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the contradiction."""

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
    provenance: list[dict[str, Any]] = field(default_factory=list)
    storage_latency: dict[str, float] = field(default_factory=dict)
    query: str = ""
    timestamp: float = field(default_factory=time.time)

    @property
    def contradiction_score(self) -> float:
        """Return a normalised contradiction score in ``[0.0, 1.0]``."""

        if self.relation_count == 0:
            return 0.0
        return min(1.0, len(self.contradictions) / self.relation_count)

    @property
    def sources(self) -> list[str]:
        """Return unique provenance sources captured during ingestion."""

        seen: dict[str, None] = {}
        for record in self.provenance:
            source = record.get("source")
            if source:
                seen[source] = None
        return list(seen.keys())

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of the summary."""

        return {
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "multi_hop_paths": [list(path) for path in self.multi_hop_paths],
            "provenance": [dict(record) for record in self.provenance],
            "storage_latency": dict(self.storage_latency),
            "sources": self.sources,
            "query": self.query,
            "timestamp": self.timestamp,
            "contradiction_score": self.contradiction_score,
        }


class SessionGraphPipeline:
    """Extract and persist knowledge graph fragments for a user session."""

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
            snippets: Iterable of snippet payloads with title, snippet, and
                optional URL metadata.

        Returns:
            A :class:`GraphExtractionSummary` describing how many entities and
            relations were added, associated provenance, and storage latency
            metrics.
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
        provenance_records: list[dict[str, Any]] = []

        for snippet in snippets:
            if len(relations) >= max_relations:
                break
            text_parts = [
                snippet.get("title"),
                snippet.get("snippet"),
                snippet.get("content"),
            ]
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
                        provenance_records.append(
                            {
                                "subject": subject.label,
                                "predicate": predicate,
                                "object": obj.label,
                                **{k: v for k, v in provenance.items() if v},
                            }
                        )
                        if len(relations) >= max_relations:
                            break
                    if len(relations) >= max_relations:
                        break

        summary = GraphExtractionSummary(
            entity_count=len(entities),
            relation_count=len(relations),
            contradictions=[],
            multi_hop_paths=[],
            provenance=provenance_records,
            storage_latency={"duckdb_seconds": 0.0, "rdf_seconds": 0.0},
            query=query,
        )

        if not relations and not entities:
            self._store_summary(summary)
            return summary

        manager = self._get_storage_manager()
        if manager is None:
            log.debug("Storage layer unavailable; skipping persistence")
            self._store_summary(summary)
            return summary

        entity_payloads = [entity.to_payload() for entity in entities.values()]
        relation_payloads = [relation.to_payload() for relation in relations]
        summary.storage_latency = self._persist_batch(
            manager,
            entities=entity_payloads,
            relations=relation_payloads,
            triples=triples,
        )

        try:
            kg_graph = manager.get_knowledge_graph(create=False)
        except Exception:  # pragma: no cover - storage errors are logged elsewhere
            kg_graph = None
        summary.contradictions = self._detect_contradictions(kg_graph)
        summary.multi_hop_paths = self._derive_multi_hop_paths(kg_graph)

        self._store_summary(summary)
        return summary

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

        manager = self._get_storage_manager()
        if manager is None:
            return []
        try:
            graph = manager.get_knowledge_graph(create=False)
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
                results.append(
                    {
                        "subject": graph.nodes[source].get("label", source),
                        "predicate": predicate,
                        "object": graph.nodes[target].get("label", target),
                        "direction": "out" if source == node else "in",
                        "target": label,
                    }
                )
                if len(results) >= limit:
                    return results
        return results

    def paths(
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

        manager = self._get_storage_manager()
        if manager is None:
            return []
        try:
            graph = manager.get_knowledge_graph(create=False)
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

    def find_paths(
        self,
        source_label: str,
        target_label: str,
        *,
        max_depth: int = 3,
        limit: int = 5,
    ) -> list[list[str]]:
        """Backward-compatible wrapper around :meth:`paths`."""

        return self.paths(source_label, target_label, max_depth=max_depth, limit=limit)

    def export_artifacts(self) -> dict[str, str]:
        """Return GraphML and JSON artefacts for downstream consumers."""

        manager = self._get_storage_manager()
        if manager is None:
            return {"graphml": "", "graph_json": "{}"}
        try:
            graphml = manager.export_knowledge_graph_graphml()
            graph_json = manager.export_knowledge_graph_json()
        except Exception:  # pragma: no cover - optional storage errors
            graphml = ""
            graph_json = "{}"
        return {"graphml": graphml, "graph_json": graph_json}

    def get_latest_summary(self) -> dict[str, Any]:
        """Return the most recent ingestion summary."""

        with self._summary_lock:
            return dict(self._latest_summary)

    def get_contradiction_score(self) -> float:
        """Return the current contradiction score from the summary."""

        summary = self.get_latest_summary()
        score = summary.get("contradiction_score")
        if isinstance(score, (int, float)):
            return float(score)
        return 0.0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_storage_manager() -> Any | None:
        """Return the storage manager or ``None`` when unavailable."""

        try:
            from ..storage import StorageManager  # Local import avoids circular dependency
        except Exception:
            return None
        return StorageManager

    def _store_summary(self, summary: GraphExtractionSummary) -> None:
        with self._summary_lock:
            self._latest_summary = summary.to_dict()

    def _ensure_entity(self, label: str, source: str | None) -> GraphEntity:
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
            manager = self._get_storage_manager()
            if manager is None:
                return []
            try:
                graph = manager.get_knowledge_graph(create=False)
            except Exception:
                return []
        if graph is None:
            return []

        buckets: dict[tuple[str, str], set[str]] = {}
        label_lookup = {node: graph.nodes[node].get("label", node) for node in graph.nodes}
        for subj, obj, key, data in graph.edges(keys=True, data=True):
            predicate = data.get("predicate") or key
            subj_label = label_lookup.get(subj, str(subj))
            obj_label = label_lookup.get(obj, str(obj))
            buckets.setdefault((subj_label, predicate), set()).add(obj_label)

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
            manager = self._get_storage_manager()
            if manager is None:
                return []
            try:
                graph = manager.get_knowledge_graph(create=False)
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
        matches: list[str] = []
        for node, attrs in graph.nodes(data=True):
            node_label = str(attrs.get("label", node)).strip().lower()
            if node_label == normalized:
                matches.append(node)
        return matches

    def _persist_batch(
        self,
        manager: Any,
        *,
        entities: Sequence[Mapping[str, Any]],
        relations: Sequence[Mapping[str, Any]],
        triples: Sequence[tuple[str, str, str]],
    ) -> dict[str, float]:
        """Persist the batch via :class:`StorageManager` and record latency."""

        duckdb_latency = 0.0
        rdf_latency = 0.0

        context = getattr(manager, "context", SimpleNamespace())
        backend = getattr(context, "db_backend", None)
        rdf_store = getattr(context, "rdf_store", None)

        backend_patches: list[tuple[Any, str, Any]] = []
        rdf_patch: tuple[Any, str, Any] | None = None

        try:
            if backend is not None:
                original_entities = backend.persist_graph_entities
                original_relations = backend.persist_graph_relations

                def timed_entities(
                    self: Any,
                    payload: Sequence[Mapping[str, Any]],
                    _original: Callable[[Sequence[Mapping[str, Any]]], Any] = original_entities,
                ) -> Any:
                    nonlocal duckdb_latency
                    start = time.monotonic()
                    try:
                        return _original(payload)
                    finally:
                        duckdb_latency += time.monotonic() - start

                def timed_relations(
                    self: Any,
                    payload: Sequence[Mapping[str, Any]],
                    _original: Callable[[Sequence[Mapping[str, Any]]], Any] = original_relations,
                ) -> Any:
                    nonlocal duckdb_latency
                    start = time.monotonic()
                    try:
                        return _original(payload)
                    finally:
                        duckdb_latency += time.monotonic() - start

                backend.persist_graph_entities = MethodType(timed_entities, backend)
                backend.persist_graph_relations = MethodType(timed_relations, backend)
                backend_patches = [
                    (backend, "persist_graph_entities", original_entities),
                    (backend, "persist_graph_relations", original_relations),
                ]

            if rdf_store is not None:
                original_add = rdf_store.add

                def timed_add(
                    self: Any,
                    triple: tuple[str, str, str],
                    _original: Callable[[tuple[str, str, str]], Any] = original_add,
                ) -> Any:
                    nonlocal rdf_latency
                    start = time.monotonic()
                    try:
                        return _original(triple)
                    finally:
                        rdf_latency += time.monotonic() - start

                rdf_store.add = MethodType(timed_add, rdf_store)
                rdf_patch = (rdf_store, "add", original_add)

            manager.update_knowledge_graph(
                entities=entities,
                relations=relations,
                triples=triples,
            )
        except Exception:  # pragma: no cover - propagation handled elsewhere
            log.debug("Knowledge graph persistence failed", exc_info=True)
        finally:
            for target, attr, original in backend_patches:
                setattr(target, attr, original)
            if rdf_patch is not None:
                target, attr, original = rdf_patch
                setattr(target, attr, original)

        return {
            "duckdb_seconds": duckdb_latency,
            "rdf_seconds": rdf_latency,
        }


__all__ = [
    "GraphContradiction",
    "GraphEntity",
    "GraphExtractionSummary",
    "GraphRelation",
    "SessionGraphPipeline",
]
